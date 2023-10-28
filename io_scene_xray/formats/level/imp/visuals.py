# addon modules
from ... import ogf
from .... import rw


def _set_hierrarhy_children(level):
    for hierrarhy_visual in level.hierrarhy_visuals:
        for child_index in hierrarhy_visual.children:
            hierrarhy_obj = level.visuals[hierrarhy_visual.index]
            child_obj = level.visuals[child_index]
            child_obj.parent = hierrarhy_obj


def import_visuals(data, level):
    chunked_reader = rw.read.ChunkedReader(data)

    for visual_id, visual_data in chunked_reader:
        ogf.imp.main.import_level_visual(visual_data, visual_id, level)

    _set_hierrarhy_children(level)
