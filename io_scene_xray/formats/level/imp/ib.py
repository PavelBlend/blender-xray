# addon modules
from .. import fmt
from ... import ogf
from .... import rw


def import_indices_buffers(level, chunks, chunks_ids):
    if level.xrlc_version <= fmt.VERSION_8:
        return

    data = chunks.pop(chunks_ids.IB)
    reader = rw.read.PackedReader(data)

    buffers_count = reader.uint32()
    level.indices_buffers = []

    for _ in range(buffers_count):
        buffer, _ = ogf.imp.indices.read_ib(reader)
        level.indices_buffers.append(buffer)
