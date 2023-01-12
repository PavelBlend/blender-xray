# addon modules
from . import header
from . import child
from . import create
from . import indices
from . import mesh
from . import utility
from . import swis
from . import gcontainer
from .. import fmt
from ... import level
from .... import rw
from .... import utils


def import_hierrarhy_visual(chunks, chunks_fmt, visual, lvl):
    if visual.format_version in (fmt.FORMAT_VERSION_2, fmt.FORMAT_VERSION_3):
        # bbox
        bbox_data = chunks.pop(chunks_fmt.BBOX)
        header.read_bbox_v3(bbox_data)

        # bsphere
        bsphere_data = chunks.pop(chunks_fmt.BSPHERE, None)
        if bsphere_data:
            header.read_bsphere_v3(bsphere_data)

    # children link
    children_l_data = chunks.pop(chunks_fmt.CHILDREN_L)
    child.import_children_l(children_l_data, visual, lvl, 'HIERRARHY')

    visual.name = 'hierrarhy'
    bpy_object = utils.create_object(visual.name, None)

    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'HIERRARHY'

    utility.check_unread_chunks(chunks, context='HIERRARHY_VISUAL')

    return bpy_object


def import_render_visual(chunks, visual, lvl, visual_type):
    bpy_mesh, geometry_key = create.import_level_geometry(chunks, visual, lvl)
    visual.name = visual_type.lower()

    if bpy_mesh:
        bpy_object = utils.create_object(visual.name, bpy_mesh)

    else:
        if visual_type == 'PROGRESSIVE':
            swi = swis.import_swidata(chunks)

            visual.indices = visual.indices[swi[0].offset : ]
            visual.indices_count = swi[0].triangles_count * 3

        indices.convert_indices_to_triangles(visual)

        bpy_object = mesh.create_visual(visual, bpy_mesh, lvl, geometry_key)

    bpy_object.xray.is_level = True
    bpy_object.xray.level.use_fastpath = visual.fastpath
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = visual_type

    utility.check_unread_chunks(chunks, context=visual_type + '_VISUAL')

    return bpy_object


def import_progressive_visual(chunks, visual, lvl):
    bpy_object = import_render_visual(chunks, visual, lvl, 'PROGRESSIVE')
    return bpy_object


def import_normal_visual(chunks, visual, lvl):
    bpy_object = import_render_visual(chunks, visual, lvl, 'NORMAL')
    return bpy_object
