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


def import_hierrarhy_visual(chunks, visual, lvl):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        chunks_ids = fmt.Chunks_v4
    elif visual.format_version in (fmt.FORMAT_VERSION_3, fmt.FORMAT_VERSION_2):

        if visual.format_version == fmt.FORMAT_VERSION_3:
            chunks_ids = fmt.Chunks_v3
        else:
            chunks_ids = fmt.Chunks_v2

        # bbox
        bbox_data = chunks.pop(chunks_ids.BBOX)
        header.read_bbox_v3(bbox_data)

        # bsphere
        bsphere_data = chunks.pop(chunks_ids.BSPHERE, None)
        if bsphere_data:
            header.read_bsphere_v3(bsphere_data)

    visual.name = 'hierrarhy'
    children_l_data = chunks.pop(chunks_ids.CHILDREN_L)
    child.import_children_l(children_l_data, visual, lvl, 'HIERRARHY')
    del children_l_data
    bpy_object = utils.create_object(visual.name, None)
    utility.check_unread_chunks(chunks, context='HIERRARHY_VISUAL')
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'HIERRARHY'
    return bpy_object


def import_progressive_visual(chunks, visual, lvl):
    visual.name = 'progressive'
    bpy_mesh, geometry_key = create.import_level_geometry(chunks, visual, lvl)
    swi = swis.import_swidata(chunks)

    visual.indices = visual.indices[swi[0].offset : ]
    visual.indices_count = swi[0].triangles_count * 3
    indices.convert_indices_to_triangles(visual)

    utility.check_unread_chunks(chunks, context='PROGRESSIVE_VISUAL')

    if not bpy_mesh:
        bpy_object = mesh.create_visual(visual, bpy_mesh, lvl, geometry_key)
        if visual.fastpath:
            bpy_object.xray.level.use_fastpath = True
        else:
            bpy_object.xray.level.use_fastpath = False
    else:
        bpy_object = utils.create_object(visual.name, bpy_mesh)

    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'PROGRESSIVE'
    return bpy_object


def import_normal_visual(chunks, visual, lvl):
    visual.name = 'normal'
    bpy_mesh, geometry_key = create.import_level_geometry(chunks, visual, lvl)
    utility.check_unread_chunks(chunks, context='NORMAL_VISUAL')

    if not bpy_mesh:
        indices.convert_indices_to_triangles(visual)
        bpy_object = mesh.create_visual(visual, bpy_mesh, lvl, geometry_key)
        if visual.fastpath:
            bpy_object.xray.level.use_fastpath = True
        else:
            bpy_object.xray.level.use_fastpath = False
    else:
        bpy_object = utils.create_object(visual.name, bpy_mesh)

    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'NORMAL'
    return bpy_object


def _import_fastpath_visual(data, visual, lvl):
    # not used function

    chunked_reader = rw.read.ChunkedReader(data)
    chunks = {}
    for chunk_id, chunkd_data in chunked_reader:
        chunks[chunk_id] = chunkd_data
    del chunked_reader

    gcontainer_chunk_data = chunks.pop(fmt.Chunks_v4.GCONTAINER)
    gcontainer.import_fastpath_gcontainer(gcontainer_chunk_data, visual, lvl)
    del gcontainer_chunk_data

    swi_chunk_data = chunks.pop(fmt.Chunks_v4.SWIDATA, None)
    if swi_chunk_data:
        packed_reader = rw.read.PackedReader(swi_chunk_data)
        swi = level.swi.import_slide_window_item(packed_reader)
        visual.indices = visual.indices[swi[0].offset : ]
        visual.indices_count = swi[0].triangles_count * 3
        del swi_chunk_data

    for chunk_id in chunks.keys():
        print('UNKNOW OGF FASTPATH CHUNK: {0:#x}'.format(chunk_id))
