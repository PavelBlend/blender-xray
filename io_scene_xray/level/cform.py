# standart modules
import os
import time

# blender modules
import bpy
import bmesh

# addon modules
from . import fmt
from . import create
from .. import utils
from .. import text
from .. import version_utils
from .. import xray_io


def import_main(context, level, data=None):
    level_cform_start_time = time.time()

    preferences = version_utils.get_preferences()
    if preferences.developer_mode:
        out = utils.print_time_info
    else:
        out = utils.print_pass
    out('import level cform', 0)

    # read level.cform file
    start_time = time.time()
    out('read file', 1)
    if level.xrlc_version >= fmt.VERSION_10:
        cform_path = os.path.join(level.path, 'level.cform')
        with open(cform_path, 'rb') as file:
            data = file.read()
    packed_reader = xray_io.PackedReader(data)
    total_time = time.time() - start_time
    out('read file', 1, total_time)

    # read header
    start_time = time.time()
    out('read header', 1)
    version = packed_reader.getf('<I')[0]
    if not version in fmt.CFORM_SUPPORT_VERSIONS:
        raise utils.AppError(text.error.cform_unsupport_ver.format(version))
    verts_count = packed_reader.getf('<I')[0]
    tris_count = packed_reader.getf('<I')[0]
    bbox_min = packed_reader.getf('<3f')
    bbox_max = packed_reader.getf('<3f')
    total_time = time.time() - start_time
    out('read header', 1, total_time)

    # read verts
    start_time = time.time()
    out('read vertices', 1)
    verts = packed_reader.get_array('f', verts_count * 3)
    verts.shape = (verts.shape[0] // 3, 3)
    total_time = time.time() - start_time
    out('read vertices', 1, total_time)

    # read game materials
    start_time = time.time()
    out('read game materials', 1)
    gamemtl_file_path = preferences.gamemtl_file_auto
    game_mtl_names = {}
    if os.path.exists(gamemtl_file_path):
        with open(gamemtl_file_path, 'rb') as gamemtl_file:
            gmtl_data = gamemtl_file.read()
        for gmtl_name, _, gmtl_id in utils.parse_gamemtl(gmtl_data):
            game_mtl_names[gmtl_id] = gmtl_name
    total_time = time.time() - start_time
    out('read game materials', 1, total_time)

    # read tris
    start_time = time.time()
    out('read triangles', 1)

    sectors_tris = {}
    sectors_verts = {}
    sectors_mats = {}    # unique sectors materials

    for sector_index in level.sectors_objects.keys():
        sectors_tris[sector_index] = []
        sectors_verts[sector_index] = set()
        sectors_mats[sector_index] = set()

    tris = [None, ] * tris_count
    unique_materials = set()

    # version 4
    if version == fmt.CFORM_VERSION_4:
        prep = packed_reader.prep('3I2H')
        for tris_index in range(tris_count):
            vert_1, vert_2, vert_3, mat, sector = packed_reader.getp(prep)
            # 14 bit material id
            mat_id = mat & 0x3fff
            # 15 bit suppress shadows
            shadows = bool(mat & 0x4000)
            # 16 bit suppress wallmarks
            wallmarks = bool(mat & 0x8000)
            tris[tris_index] = (
                vert_1, vert_2, vert_3,
                mat_id, shadows, wallmarks
            )
            unique_materials.add((mat_id, shadows, wallmarks))
            sectors_tris[sector].append(tris_index)
            sectors_verts[sector].update((vert_1, vert_2, vert_3))
            sectors_mats[sector].add((mat_id, shadows, wallmarks))

    # version 2 or 3
    elif version in (fmt.CFORM_VERSION_2, fmt.CFORM_VERSION_3):
        prep = packed_reader.prep('6I2HI')
        for tris_index in range(tris_count):
            (
                vert_1, vert_2, vert_3,
                _, _, _, _,
                sector, mat_id
            ) = packed_reader.getp(prep)
            shadows = False
            wallmarks = False
            tris[tris_index] = (
                vert_1, vert_2, vert_3,
                mat_id, shadows, wallmarks
            )
            unique_materials.add((mat_id, shadows, wallmarks))
            sectors_tris[sector].append(tris_index)
            sectors_verts[sector].update((vert_1, vert_2, vert_3))
            sectors_mats[sector].add((mat_id, shadows, wallmarks))

    # sector sets to lists
    for sector_index in sectors_tris.keys():
        sectors_mats[sector_index] = list(sectors_mats[sector_index])
        sectors_verts[sector_index] = list(sectors_verts[sector_index])

    total_time = time.time() - start_time
    out('read triangles', 1, total_time)

    # create bpy materials
    start_time = time.time()
    out('create materials', 1)
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

    total_time = time.time() - start_time
    out('create materials', 1, total_time)

    # create geometry
    create_geometry_start_time = time.time()
    out('create geometry', 1)
    create_verts_time = 0.0
    create_tris_time = 0.0
    create_verts_2_time = 0.0
    create_tris_2_time = 0.0
    create_objects_time = 0.0
    out()

    for sector, triangles in sectors_tris.items():

        # create verts
        sector_start_time = time.time()
        start_time = time.time()
        message = 'sector_{0:0>3} create vertices'.format(sector)
        out(message, 3)
        sector_verts = sectors_verts[sector]
        bm = bmesh.new()
        remap_verts = {}
        for remap_vertex_index, vert_index in enumerate(sector_verts):
            vert_co = verts[vert_index]
            bm.verts.new((vert_co[0], vert_co[2], vert_co[1]))
            remap_verts[vert_index] = remap_vertex_index
        verts_count = remap_vertex_index + 1
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        total_time = time.time() - start_time
        out(message, 3, total_time)
        create_verts_time += total_time

        # create tris
        start_time = time.time()
        message = 'sector_{0:0>3} create triangles'.format(sector)
        out(message, 3)

        tris_2 = []    # two sided tris
        verts_2 = set()    # two sided verts
        for tris_index in triangles:
            vert_1, vert_2, vert_3, mat_id, shadow, wm = tris[tris_index]
            try:
                face = bm.faces.new((
                    bm.verts[remap_verts[vert_1]],
                    bm.verts[remap_verts[vert_3]],
                    bm.verts[remap_verts[vert_2]]
                ))
                material = sectors_mats[sector].index((mat_id, shadow, wm))
                face.material_index = material
                face.smooth = True
            except ValueError:
                face = None
                tris_2.append((vert_1, vert_2, vert_3, mat_id, shadow, wm))
                verts_2.update((vert_1, vert_2, vert_3))

        total_time = time.time() - start_time
        out(message, 3, total_time)
        create_tris_time += total_time

        # create two sided verts
        start_time = time.time()
        message = 'sector_{0:0>3} create two sided vertices'.format(sector)
        out(message, 3)
        remap_vertices = {}
        for remap_vert_index, vertex_index in enumerate(verts_2):
            vert_co = verts[vertex_index]
            bm.verts.new((vert_co[0], vert_co[2], vert_co[1]))
            remap_vertices[vertex_index] = remap_vert_index + verts_count
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        total_time = time.time() - start_time
        out(message, 3, total_time)
        create_verts_2_time += total_time

        # create two sided tris
        start_time = time.time()
        message = 'sector_{0:0>3} create two sided triangles'.format(sector)
        out(message, 3)
        for vert_1, vert_2, vert_3, mat_id, shadow, wm in tris_2:
            try:
                face = bm.faces.new((
                    bm.verts[remap_vertices[vert_1]],
                    bm.verts[remap_vertices[vert_3]],
                    bm.verts[remap_vertices[vert_2]]
                ))
                mat = sectors_mats[sector].index((mat_id, shadow, wm))
                face.material_index = mat
                face.smooth = True
            except ValueError:    # face already exists
                pass
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        bm.normal_update()
        total_time = time.time() - start_time
        out(message, 3, total_time)
        create_tris_2_time += total_time

        start_time = time.time()
        message = 'sector_{0:0>3} create object'.format(sector)
        out(message, 3)

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
        if not version_utils.IS_28:
            version_utils.link_object(bpy_obj)

        total_time = time.time() - start_time
        out(message, 3, total_time)
        create_objects_time += total_time

        out()
        message = 'sector_{0:0>3} total time'.format(sector)
        sector_total_time = time.time() - sector_start_time
        out(message, 3, sector_total_time)
        create_objects_time += total_time
        out()


    out('create vertices', 2, create_verts_time)
    out('create triangles', 2, create_tris_time)
    out('create two-sided vertices', 2, create_verts_2_time)
    out('create two-sided triangles', 2, create_tris_2_time)
    out('create objects', 2, create_objects_time)
    total_time = time.time() - create_geometry_start_time
    out('create geometry', 1, total_time)

    total_time = time.time() - level_cform_start_time
    out('import level cform', 0, total_time)
