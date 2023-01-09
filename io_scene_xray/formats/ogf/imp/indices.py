# addon modules
from .... import rw


def read_indices(packed_reader):
    indices_count = packed_reader.getf('<I')[0]
    indices_buffer = packed_reader.getf('<{0}H'.format(indices_count))
    return indices_buffer, indices_count


def import_indices(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.INDICES)
    packed_reader = rw.read.PackedReader(chunk_data)
    visual.indices, visual.indices_count = read_indices(packed_reader)


def read_indices_v3(data, visual):
    packed_reader = rw.read.PackedReader(data)
    indices_count = packed_reader.getf('<I')[0]
    visual.indices_count = indices_count
    visual.indices = [
        packed_reader.getf('<H')[0]
        for index in range(indices_count)
    ]


def convert_indices_to_triangles(visual):
    visual.triangles = []
    for index in range(0, visual.indices_count, 3):
        visual.triangles.append((
            visual.indices[index],
            visual.indices[index + 2],
            visual.indices[index + 1]
        ))
    del visual.indices
    del visual.indices_count
