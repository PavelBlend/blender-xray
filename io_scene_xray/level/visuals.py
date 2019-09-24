from .. import xray_io
from ..ogf import imp


def import_visuals(data, materials):
    chunked_reader = xray_io.ChunkedReader(data)

    for visual_id, visual_data in chunked_reader:
        imp.import_(visual_data, materials)
