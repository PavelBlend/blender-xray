# addon modules
from . import types
from .... import rw


def import_children_l(data, visual, lvl, visual_type):
    packed_reader = rw.read.PackedReader(data)

    hierrarhy_visual = types.HierrarhyVisual()
    hierrarhy_visual.children_count = packed_reader.getf('<I')[0]
    hierrarhy_visual.index = visual.visual_id
    hierrarhy_visual.visual_type = visual_type

    if len(data) == 4 + 4 * hierrarhy_visual.children_count:
        child_format = 'I'

    elif len(data) == 4 + 2 * hierrarhy_visual.children_count:
        # used in agroprom 2215 (version 13)
        child_format = 'H'

    else:
        raise BaseException('Bad OGF CHILDREN_L data')

    for child_index in range(hierrarhy_visual.children_count):
        child = packed_reader.getf('<' + child_format)[0]
        hierrarhy_visual.children.append(child)

    lvl.hierrarhy_visuals.append(hierrarhy_visual)
