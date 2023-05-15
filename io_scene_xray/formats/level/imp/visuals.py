# addon modules
from ... import ogf
from .... import rw


def import_hierrarhy_visuals(level):
    for hierrarhy_visual in level.hierrarhy_visuals:
        for child_index in hierrarhy_visual.children:
            hierrarhy_obj = level.visuals[hierrarhy_visual.index]
            child_obj = level.visuals[child_index]
            child_obj.parent = hierrarhy_obj


def import_visuals(data, level):
    chunked_reader = rw.read.ChunkedReader(data)
    chunks = set()
    visuals_ids = set()
    for visual_id, visual_data in chunked_reader:
        visuals_ids.add(visual_id)
        ogf.imp.main.import_level_visual(
            visual_data,
            visual_id,
            level,
            chunks,
            visuals_ids
        )
    chunks = list(chunks)
    chunks.sort()
