# addon modules
from .... import rw


def read_bone_names(chunks, chunks_ids, visual):
    chunk_data = chunks.pop(chunks_ids.S_BONE_NAMES)
    packed_reader = rw.read.PackedReader(chunk_data)

    bones_count = packed_reader.uint32()

    for bone_index in range(bones_count):
        bone_name = packed_reader.gets()
        bone_parent = packed_reader.gets()

        rotation = packed_reader.getf('<9f')
        translation = packed_reader.getf('<3f')
        half_size = packed_reader.getf('<3f')

        visual.bones.append((bone_name, bone_parent))
        visual.bones_indices[bone_index] = bone_name
