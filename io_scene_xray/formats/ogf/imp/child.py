# standart modules
import struct

# addon modules
from . import types
from . import main
from . import utility
from .... import rw


INT32_LEN = struct.calcsize('<I')
INT16_LEN = struct.calcsize('<H')


def import_children_l(data, visual, lvl, visual_type):
    reader = rw.read.PackedReader(data)

    hier_vis = types.HierrarhyVisual()
    hier_vis.children_count = reader.uint32()
    hier_vis.index = visual.visual_id
    hier_vis.visual_type = visual_type
    lvl.hierrarhy_visuals.append(hier_vis)

    data_len = len(data) - INT32_LEN    # subtruct children count

    if data_len == INT32_LEN * hier_vis.children_count:
        child_format = 'I'

    elif data_len == INT16_LEN * hier_vis.children_count:
        # used in agroprom 2215 (version 13)
        child_format = 'H'

    else:
        raise BaseException('Bad OGF CHILDREN_L data')

    hier_vis.children = reader.getf('<{0}{1}'.format(
        hier_vis.children_count,
        child_format
    ))


def import_children(context, chunks, chunks_ids, root_visual):
    chunk_data = chunks.pop(chunks_ids.CHILDREN, None)

    if chunk_data:
        chunked_reader = rw.read.ChunkedReader(chunk_data)

        for child_index, child_data in chunked_reader:
            visual = types.Visual()
            visual.file_path = root_visual.file_path
            visual.name = root_visual.name + ' {:0>2}'.format(child_index)
            visual.visual_id = child_index
            visual.is_root = False
            visual.arm_obj = root_visual.arm_obj
            visual.root_obj = root_visual.root_obj
            visual.bones = root_visual.bones

            main.import_ogf_visual(context, child_data, visual)

            utility.set_visual_type(visual, root_visual)
