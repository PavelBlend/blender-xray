from .. import xray_io
from ..ogf import imp


def import_visuals(data, vertex_buffers, indices_buffers, swis, materials):
    chunked_reader = xray_io.ChunkedReader(data)

    chunks = set()
    for visual_id, visual_data in chunked_reader:
        imp.import_(
            visual_data, materials, vertex_buffers, indices_buffers, swis, chunks
        )
    chunks = list(chunks)
    chunks.sort()
    for i in chunks:
        print(i)
