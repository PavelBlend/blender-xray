# standart modules
import os
import time

# blender modules
import bpy
import bmesh

# addon modules
from .. import xray_io, utils, plugin_prefs, prefs
from . import fmt, create


def import_main(context, level, data=None):
    start_time = time.time()

    # read level.cform file
    if level.xrlc_version >= fmt.VERSION_10:
        cform_path = os.path.join(level.path, 'level.cform')
        with open(cform_path, 'rb') as file:
            data = file.read()
    packed_reader = xray_io.PackedReader(data)

    # read header
    version = packed_reader.getf('<I')[0]
    if not version in fmt.CFORM_SUPPORT_VERSIONS:
        raise utils.AppError('Unsupported cform version: {}'.format(version))
    verts_count = packed_reader.getf('<I')[0]
    tris_count = packed_reader.getf('<I')[0]
    bbox_min = packed_reader.getf('<3f')
    bbox_max = packed_reader.getf('<3f')

    # read verts
    verts = []
    for vert_index in range(verts_count):
        vert_co_x, vert_co_y, vert_co_z = packed_reader.getf('<3f')
        verts.append((vert_co_x, vert_co_z, vert_co_y))

    # read game materials
    preferences = prefs.utils.get_preferences()
    gamemtl_file_path = preferences.gamemtl_file_auto
    game_mtl_names = {}
    if os.path.exists(gamemtl_file_path):
        with open(gamemtl_file_path, 'rb') as gamemtl_file:
            gmtl_data = gamemtl_file.read()
        for gmtl_name, _, gmtl_id in utils.parse_gamemtl(gmtl_data):
            game_mtl_names[gmtl_id] = gmtl_name

    # read face code
    if version == fmt.CFORM_VERSION_4:
        code = ''
        # sector index
        code += 'material, sector = packed_reader.getf("<2H")\n'
        code += 'globals()["sector"] = sector\n'
        # 14 bit material id
        code += 'globals()["mat_id"] = material & 0x3fff\n'
        # 15 bit suppress shadows
        code += 'globals()["shadows"] = bool((material & 0x4000) >> 14)\n'
        # 16 bit suppress wallmarks
        code += 'globals()["wallmarks"] = bool((material & 0x8000) >> 15)\n'
    elif version in (fmt.CFORM_VERSION_3, fmt.CFORM_VERSION_2):
        code = ''
        code += 'packed_reader.skip(12 + 2)\n'    # ?
        code += 'globals()["sector"] = packed_reader.getf("<H")[0]\n'
        code += 'globals()["mat_id"] = packed_reader.getf("<I")[0]\n'
        code += 'globals()["shadows"] = False\n'
        code += 'globals()["wallmarks"] = False\n'

    # read tris
    sectors_tris = {}
    sectors_verts = {}
    # unique sectors materials
    sectors_mats = {}
    tris = []
    unique_materials = set()
    for tris_index in range(tris_count):
        vert_1, vert_2, vert_3 = packed_reader.getf('<3I')
        exec(code)
        global mat_id, sector, shadows, wallmarks
        tris.append((vert_1, vert_2, vert_3, mat_id, shadows, wallmarks))
        unique_materials.add((mat_id, shadows, wallmarks))
        if not sectors_tris.get(sector):
            sectors_tris[sector] = []
            sectors_verts[sector] = set()
            sectors_mats[sector] = set()
        sectors_tris[sector].append(tris_index)
        sectors_verts[sector].update((vert_1, vert_2, vert_3))
        sectors_mats[sector].add((mat_id, shadows, wallmarks))

    # sort sector materials
    for sector_index, sector_materials in sectors_mats.items():
        sector_materials = list(sector_materials)
        sector_materials.sort()
        sectors_mats[sector_index] = sector_materials

    # create bpy materials
    bpy_materials = {}
    for mat_id, shadows, wallmarks in unique_materials:
        gmtl = game_mtl_names.get(mat_id, str(mat_id))
        mat_name = '{0}_{1}_{2}'.format(gmtl, int(shadows), int(wallmarks))

        # search material
        material = None
        for bpy_mat in bpy.data.materials:
            if not bpy_mat.name.startswith(mat_name):
                continue
            xray = bpy_mat.xray
            if not xray.gamemtl == gamemtl_name:
                continue
            if not xray.suppress_shadows == shadows:
                continue
            if not xray.suppress_wm == wallmarks:
                continue
            material = bpy_mat

        # create material
        if not material:
            material = bpy.data.materials.new(mat_name)
            material.xray.version = context.version
            material.xray.eshader = 'default'
            material.xray.cshader = 'default'
            material.xray.gamemtl = gmtl
            material.xray.suppress_shadows = shadows
            material.xray.suppress_wm = wallmarks

        bpy_materials[mat_id] = material

    # create geometry
    for sector, triangles in sectors_tris.items():

        # create verts
        sector_verts = sectors_verts[sector]
        sector_verts = list(sector_verts)
        sector_verts.sort()
        bm = bmesh.new()
        current_vertex_index = 0
        remap_verts = {}
        for vert_index in sector_verts:
            vert_co = verts[vert_index]
            bm.verts.new(vert_co)
            remap_verts[vert_index] = current_vertex_index
            current_vertex_index += 1
        vertices_count = current_vertex_index
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        # create tris

        # two sided tris
        tris_2 = []
        # two sided verts
        verts_2 = set()
        for tris_index in triangles:
            vert_1, vert_2, vert_3, mat_id, shadow, wm = tris[tris_index]
            try:
                face = bm.faces.new((
                    bm.verts[remap_verts[vert_1]],
                    bm.verts[remap_verts[vert_3]],
                    bm.verts[remap_verts[vert_2]]
                ))
                face.smooth = True
                material = sectors_mats[sector].index((mat_id, shadow, wm))
                face.material_index = material
            except ValueError:
                face = None
                tris_2.append((vert_1, vert_2, vert_3, mat_id, shadow, wm))
                verts_2.update((vert_1, vert_2, vert_3))

        # create two sided verts
        current_vertex_index = vertices_count
        remap_vertices = {}
        for vertex_index in sorted(list(verts_2)):
            vert_co = verts[vertex_index]
            bm.verts.new(vert_co)
            remap_vertices[vertex_index] = current_vertex_index
            current_vertex_index += 1
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        # create two sided tris
        for vert_1, vert_2, vert_3, mat_id, shadow, wm in tris_2:
            try:
                face = bm.faces.new((
                    bm.verts[remap_vertices[vert_1]],
                    bm.verts[remap_vertices[vert_3]],
                    bm.verts[remap_vertices[vert_2]]
                ))
                face.smooth = True
                mat = sectors_mats[sector].index((mat_id, shadow, wm))
                face.material_index = mat
            except ValueError:    # face already exists
                pass
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        bm.normal_update()

        # create mesh
        obj_name = 'cform_{:0>3}'.format(sector)
        bpy_mesh = bpy.data.meshes.new(obj_name)

        # append materials
        for mat_id, _, _ in sectors_mats[sector]:
            bpy_material = bpy_materials[mat_id]
            bpy_mesh.materials.append(bpy_material)

        # create object
        bm.to_mesh(bpy_mesh)
        bpy_obj = bpy.data.objects.new(obj_name, bpy_mesh)
        bpy_obj.parent = level.sectors_objects[sector]
        bpy_obj.xray.is_level = True
        bpy_obj.xray.level.object_type = 'CFORM'
        collection = level.collections[create.LEVEL_CFORM_COLLECTION_NAME]
        collection.objects.link(bpy_obj)

    # statistics
    STATISTICS = False
    end_time = time.time()
    total_time = end_time - start_time
    if STATISTICS:
        print('Import CForm Time: {0:.3f} seconds'.format(total_time))
