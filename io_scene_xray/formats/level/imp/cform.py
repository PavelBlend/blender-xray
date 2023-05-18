# standart modules
import os

# blender modules
import bpy
import bmesh

# addon modules
from . import create
from .. import fmt
from ... import xr
from .... import utils
from .... import log
from .... import text
from .... import rw


def import_main(context, level, cform_path, data):
    # get reader
    packed_reader = rw.read.PackedReader(data)

    # read header
    version = packed_reader.uint32()
    if not version in fmt.CFORM_SUPPORT_VERSIONS:
        raise log.AppError(
            text.error.cform_unsupport_ver,
            log.props(version=version, file=cform_path)
        )
    verts_count = packed_reader.uint32()
    tris_count = packed_reader.uint32()
    bbox_min = packed_reader.getf('<3f')
    bbox_max = packed_reader.getf('<3f')

    # read verts
    verts = packed_reader.get_array('f', verts_count, vec_len=3)

    # read game materials
    pref = utils.version.get_preferences()
    gamemtl_file_path = pref.gamemtl_file_auto
    game_mtl_names = {}
    if os.path.exists(gamemtl_file_path):
        gmtl_data = rw.utils.read_file(gamemtl_file_path)
        for gmtl_name, _, gmtl_id in xr.parse_gamemtl(gmtl_data):
            game_mtl_names[gmtl_id] = gmtl_name

    # read tris
    sectors_tris = {}
    sectors_verts = {}
    sectors_mats = {}    # unique sectors materials
    for sector_index in level.sectors_objects.keys():
        sectors_tris[sector_index] = []
        sectors_verts[sector_index] = set()
        sectors_mats[sector_index] = set()
    tris = [None, ] * tris_count
    unique_materials = set()

    # faces in version 4
    if version == fmt.CFORM_VERSION_4:
        prep = packed_reader.prep('3I2H')
        for tris_index in range(tris_count):
            vert_1, vert_2, vert_3, mat, sector = packed_reader.getp(prep)
            # 0-14 bits material id
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

    # faces in version 2 or 3
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
    for sector_index in sectors_tris:
        sectors_mats[sector_index] = list(sectors_mats[sector_index])
        sectors_verts[sector_index] = list(sectors_verts[sector_index])

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
            if not xray.gamemtl == gmtl:
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
        bm = bmesh.new()
        remap_verts = {}
        for remap_vertex_index, vert_index in enumerate(sector_verts):
            vert_co = verts[vert_index]
            bm.verts.new((vert_co[0], vert_co[2], vert_co[1]))
            remap_verts[vert_index] = remap_vertex_index
        verts_count = remap_vertex_index + 1
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        # create tris
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

        # create two sided verts
        remap_vertices = {}
        for remap_vert_index, vertex_index in enumerate(verts_2):
            vert_co = verts[vertex_index]
            bm.verts.new((vert_co[0], vert_co[2], vert_co[1]))
            remap_vertices[vertex_index] = remap_vert_index + verts_count
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
                mat = sectors_mats[sector].index((mat_id, shadow, wm))
                face.material_index = mat
                face.smooth = True
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
        bpy_obj.xray.version = level.addon_version
        bpy_obj.xray.isroot = False
        bpy_obj.xray.is_level = True
        bpy_obj.xray.level.object_type = 'CFORM'
        collection = level.collections[create.LEVEL_CFORM_COLLECTION_NAME]
        collection.objects.link(bpy_obj)
        if not utils.version.IS_28:
            utils.version.link_object(bpy_obj)
