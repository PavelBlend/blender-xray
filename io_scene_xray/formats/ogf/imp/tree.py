# blender modules
import mathutils

# addon modules
from . import create
from . import indices
from . import mesh
from . import swis
from . import utility
from .. import fmt
from ... import level
from .... import rw
from .... import utils


def set_tree_transforms(bpy_object, xform):
    transform_matrix = mathutils.Matrix((
        (xform[0], xform[1], xform[2], xform[3]),
        (xform[4], xform[5], xform[6], xform[7]),
        (xform[8], xform[9], xform[10], xform[11]),
        (xform[12], xform[13], xform[14], xform[15])
    ))
    # transpose DirectX transformation matrix for OpenGL
    transform_matrix.transpose()

    translate, rotate, scale = transform_matrix.decompose()
    rotate = rotate.to_euler('ZXY')

    bpy_object.location = translate[0], translate[2], translate[1]
    bpy_object.rotation_euler = -rotate[0], -rotate[2], -rotate[1]
    bpy_object.scale = scale[0], scale[2], scale[1]


def import_tree_def_2(lvl, visual, chunks, bpy_object):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        chunks_ids = fmt.Chunks_v4
    elif visual.format_version == fmt.FORMAT_VERSION_3:
        chunks_ids = fmt.Chunks_v3

    tree_def_2_data = chunks.pop(chunks_ids.TREEDEF2)
    packed_reader = rw.read.PackedReader(tree_def_2_data)

    tree_xform = packed_reader.getf('<16f')
    set_tree_transforms(bpy_object, tree_xform)

    read_tree_color(lvl, packed_reader, bpy_object, True)    # c_scale
    read_tree_color(lvl, packed_reader, bpy_object, False)    # c_bias


def read_tree_color(lvl, packed_reader, bpy_obj, is_scale_mode):
    params = bpy_obj.xray.level

    if lvl.xrlc_version >= level.fmt.VERSION_11:
        rgb = packed_reader.getf('<3f')
        hemi = packed_reader.getf('<f')[0]
        sun = packed_reader.getf('<f')[0]
    else:
        rgb = packed_reader.getf('<3f')
        hemi = packed_reader.getf('<f')[0]    # unkonwn
        sun = 1.0

    if is_scale_mode:
        params.color_scale_rgb = rgb
        params.color_scale_hemi = (hemi, hemi, hemi)
        params.color_scale_sun = (sun, sun, sun)
    else:
        params.color_bias_rgb = rgb
        params.color_bias_hemi = (hemi, hemi, hemi)
        params.color_bias_sun = (sun, sun, sun)


def import_tree_pm_visual(chunks, visual, lvl):
    visual.name = 'tree_pm'
    bpy_mesh, geometry_key = create.import_level_geometry(chunks, visual, lvl)

    swi_index = swis.import_swicontainer(chunks)

    if bpy_mesh:
        bpy_object = utils.obj.create_object(visual.name, bpy_mesh)

    else:
        swi = lvl.swis[swi_index]

        visual.indices = visual.indices[swi[0].offset : ]
        visual.indices_count = swi[0].triangles_count * 3

        indices.convert_indices_to_triangles(visual)

        bpy_object = mesh.create_visual(visual, lvl, geometry_key)

    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'TREE_PM'

    import_tree_def_2(lvl, visual, chunks, bpy_object)

    utility.check_unread_chunks(chunks, context='TREE_PM_VISUAL')

    return bpy_object


def import_tree_st_visual(chunks, visual, lvl):
    visual.name = 'tree_st'
    bpy_mesh, geometry_key = create.import_level_geometry(chunks, visual, lvl)

    if bpy_mesh:
        bpy_object = utils.obj.create_object(visual.name, bpy_mesh)
    else:
        indices.convert_indices_to_triangles(visual)
        bpy_object = mesh.create_visual(visual, lvl, geometry_key)

    xray = bpy_object.xray
    xray.is_level = True
    xray.level.object_type = 'VISUAL'
    xray.level.visual_type = 'TREE_ST'

    import_tree_def_2(lvl, visual, chunks, bpy_object)

    utility.check_unread_chunks(chunks, context='TREE_ST_VISUAL')

    return bpy_object
