# addon modules
from .... import rw


def read_ib(packed_reader):
    indices_count = packed_reader.uint32()
    indices_buffer = packed_reader.getf('<{0}H'.format(indices_count))
    return indices_buffer, indices_count


def read_indices(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.INDICES)
    packed_reader = rw.read.PackedReader(chunk_data)
    visual.indices, visual.indices_count = read_ib(packed_reader)


def convert_indices_to_triangles(visual):
    for index in range(0, visual.indices_count, 3):
        visual.triangles.append((
            visual.indices[index],
            visual.indices[index + 2],
            visual.indices[index + 1]
        ))

    visual.indices.clear()
