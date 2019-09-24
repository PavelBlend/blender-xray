from .. import xray_io


def import_(data, materials=None):
    chunked_reader = xray_io.ChunkedReader(data)
    for chunk_id, chunkd_data in chunked_reader:
        pass
