# addon modules
from ... import ogf
from .... import rw


def import_indices_buffers(data):
    reader = rw.read.PackedReader(data)

    buffers = []
    buffers_count = reader.uint32()

    for index in range(buffers_count):
        buffer, _ = ogf.imp.indices.read_ib(reader)
        buffers.append(buffer)

    return buffers
