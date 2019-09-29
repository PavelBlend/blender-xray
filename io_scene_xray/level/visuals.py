from .. import xray_io
from ..ogf import imp


def import_hierrarhy_visuals(level):
    for hierrarhy_visual in level.hierrarhy_visuals:
        for child_index in hierrarhy_visual.children:
            hierrarhy_obj = level.visuals[hierrarhy_visual.index]
            child_obj = level.visuals[child_index]
            child_obj.parent = hierrarhy_obj


def import_visuals(data, level):
    chunked_reader = xray_io.ChunkedReader(data)

    chunks = set()
    for visual_id, visual_data in chunked_reader:
        imp.import_(visual_data, visual_id, level, chunks)
    chunks = list(chunks)
    chunks.sort()
    for i in chunks:
        print(i)
