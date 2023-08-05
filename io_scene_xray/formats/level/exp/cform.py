# standart modules
import os

# blender modules
import bmesh

# addon modules
from .. import fmt
from ... import xr
from .... import text
from .... import utils
from .... import log
from .... import rw


def get_bbox(bbox_1, bbox_2, function):
    if not bbox_1:
        return bbox_2
    bbox_x = function(bbox_1[0], bbox_2[0])
    bbox_y = function(bbox_1[1], bbox_2[1])
    bbox_z = function(bbox_1[2], bbox_2[2])
    return (bbox_x, bbox_y, bbox_z)


def write_cform(file_path, level):
    materials = set()
    bbox_min = None
    bbox_max = None

    for cform_object in level.cform_objects.values():
        # find min/max bbox
        bbox_min = get_bbox(bbox_min, cform_object.bound_box[0], min)
        bbox_max = get_bbox(bbox_max, cform_object.bound_box[6], max)
        # collect materials
        for material in cform_object.data.materials:
            if material:
                materials.add(material)

    # get gamemtl.xr data
    pref = utils.version.get_preferences()
    game_mtl_files = utils.ie.get_pref_paths('gamemtl_file')
    gamemtl_data = None

    for game_mtl_file in game_mtl_files:
        if os.path.exists(game_mtl_file):
            gamemtl_data = rw.utils.read_file(game_mtl_file)
            break

    # read gamemtl.xr
    gamemtl_ids = {}
    if gamemtl_data:
        for gamemtl_name, _, gamemtl_id in xr.parse_gamemtl(gamemtl_data):
            gamemtl_ids[gamemtl_name] = gamemtl_id

    # find game material ids
    game_materials = {}
    for material in materials:
        gamemtl = material.xray.gamemtl
        gamemtl_id = gamemtl_ids.get(gamemtl, None)
        # game material id by gamemtl name
        if gamemtl_id is None:
            if gamemtl.isdigit():
                gamemtl_id = int(gamemtl)
        # game material id by material name
        if gamemtl_id is None:
            prefix = material.name.split('_')[0]
            if prefix.isdigit():
                gamemtl_id = int(prefix)
            else:
                gamemtl_id = 0
        game_materials[material.name] = gamemtl_id

    # write geometry
    tris_count = 0
    verts_count = 0

    verts_writer = rw.write.PackedWriter()
    tris_writer = rw.write.PackedWriter()

    sectors_count = len(level.cform_objects)

    for sector_index in range(sectors_count):
        cform_object = level.cform_objects[sector_index]

        # create bmesh and triangulate
        bm = bmesh.new()
        bm.from_mesh(cform_object.data)
        bmesh.ops.triangulate(bm, faces=bm.faces)

        # write vertices
        for vert in bm.verts:
            verts_writer.putf('<3f', vert.co.x, vert.co.z, vert.co.y)

        # write triangles
        for face in bm.faces:

            # write vertex indices
            vert_1, vert_2, vert_3 = face.verts
            tris_writer.putf(
                '<3I',
                vert_1.index + verts_count,
                vert_3.index + verts_count,
                vert_2.index + verts_count
            )

            # write material and sector
            mat = cform_object.data.materials[face.material_index]
            if not mat:
                raise log.AppError(
                    text.error.level_cform_empty_mat_slot,
                    log.props(
                        cform_object=cform_object.name,
                        material_slot_index=face.material_index
                    )
                )
            material_id = game_materials[mat.name]
            suppress_shadows = (int(mat.xray.suppress_shadows) << 14) & 0x4000
            suppress_wm = (int(mat.xray.suppress_wm) << 15) & 0x8000
            tris_attributes = material_id | suppress_shadows | suppress_wm
            tris_writer.putf('<2H', tris_attributes, sector_index)

        verts_count += len(bm.verts)
        tris_count += len(bm.faces)

    # write header
    header_writer = rw.write.PackedWriter()
    header_writer.putf('<I', fmt.CFORM_VERSION_4)
    header_writer.putf('<I', verts_count)
    header_writer.putf('<I', tris_count)
    header_writer.putf('<3f', bbox_min[0], bbox_min[2], bbox_min[1])
    header_writer.putf('<3f', bbox_max[0], bbox_max[2], bbox_max[1])

    # write cform
    cform_writer = rw.write.PackedWriter()
    cform_writer.putp(header_writer)
    cform_writer.putp(verts_writer)
    cform_writer.putp(tris_writer)

    # save file
    cform_path = file_path + os.extsep + 'cform'
    rw.utils.save_file(cform_path, cform_writer)
