# addon modules
from .. import ogf
from .. import xray_io


def import_indices_buffers(data):
    packed_reader = xray_io.PackedReader(data)
    indices_buffers_count = packed_reader.getf('<I')[0]
    indices_buffers = []
    for indices_buffer_index in range(indices_buffers_count):
        indices_buffer = ogf.imp.read_indices(packed_reader)
        indices_buffers.append(indices_buffer)
    return indices_buffers
