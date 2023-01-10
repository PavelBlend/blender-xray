# addon modules
from .. import ogf
from ... import rw


def import_indices_buffers(data):
    packed_reader = rw.read.PackedReader(data)
    indices_buffers_count = packed_reader.getf('<I')[0]
    indices_buffers = []
    for indices_buffer_index in range(indices_buffers_count):
        indices_buffer, indices_count = ogf.imp.indices.get_indices(packed_reader)
        indices_buffers.append(indices_buffer)
    return indices_buffers
