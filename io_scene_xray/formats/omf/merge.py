# standart modules
import struct

# addon modules
from .. import ogf
from .. import omf
from ... import rw


class OmfMotion:
    def __init__(self):
        self.file = None
        self.name = None

        self.motion_offset = None
        self.motion_end = None

        self.params_offset = None
        self.params_end = None

        self.id_offset = None


class OmfParts:
    def __init__(self):
        self.data = None
        self.offset = None
        self.size = None


class OmfFile:
    def __init__(self):
        self.file = None
        self.data = None
        self.motion_count = None
        self.motions = {}


# data size
CRC32_SZ = 4
QUAT_16_SZ = 4 * 2    # x, y, z, w 16 bit
TRN_8_SZ = 3 * 1    # x, y, z 8 bit
TRN_16_SZ = 3 * 2    # x, y, z 16 bit
TRN_FLOAT_SZ = 3 * 4    # x, y, z float
TRN_INIT_SZ = 3 * 4    # x, y, z float
TRN_SIZE_SZ = 3 * 4    # x, y, z float


def merge_files(files):
    required_params_ver = None
    required_part_count = None
    required_part_names = None
    required_part_bone_names = None
    required_part_bone_ids = None
    required_bones_count = 0

    omf_files = []

    for file_index, file in enumerate(files):

        # read file
        with open(file, 'rb') as file:
            file_data = bytearray(file.read())

        reader = rw.read.PackedReader(file_data)
        omf_file = OmfFile()
        omf_file.file = file
        omf_file.data = file_data
        omf_files.append(omf_file)

        while not reader.is_end():
            chunk_id, chunk_size = reader.getf('<2I')

            # read params chunk
            if chunk_id == ogf.fmt.Chunks_v4.S_SMPARAMS_1:

                parts_offset = reader.offset()

                # read header
                params_ver = reader.getf('<H')[0]
                if not params_ver in (3, 4):
                    raise 'ver'

                # read bone parts
                parts_count = reader.getf('<H')[0]

                part_names = []
                part_bone_names = {}
                part_bone_ids = {}

                for part_id in range(parts_count):
                    part_name = reader.gets().lower()
                    bone_count = reader.getf('<H')[0]
                    part_names.append(part_name)
                    part_bone_names[part_name] = []
                    part_bone_ids[part_name] = []

                    if not file_index:
                        required_bones_count += bone_count

                    for bone in range(bone_count):
                        bone_name = reader.gets().lower()
                        bone_id = reader.uint32()
                        part_bone_names[part_name].append(bone_name)
                        part_bone_ids[part_name].append(bone_id)

                # check bone parts
                if file_index:
                    if required_params_ver != params_ver:
                        raise 'params_ver'

                    if required_part_count != parts_count:
                        raise 'parts_count'

                    if required_part_names != part_names:
                        raise 'part_names'

                    for part_name in required_part_names:
                        req_bone_names = required_part_bone_names[part_name]
                        bone_names = part_bone_names[part_name]
                        if req_bone_names != bone_names:
                            raise 'part_bone_names'

                    for part_name in required_part_names:
                        req_bone_ids = required_part_bone_ids[part_name]
                        bone_ids = part_bone_ids[part_name]
                        if req_bone_ids != bone_ids:
                            raise 'part_bone_ids'

                else:
                    required_params_ver = params_ver
                    required_part_count = parts_count
                    required_part_names = part_names
                    required_part_bone_names = part_bone_names
                    required_part_bone_ids = part_bone_ids

                    omf_parts = OmfParts()
                    omf_parts.data = file_data
                    omf_parts.start = parts_offset
                    omf_parts.end = reader.offset()

                # read motions
                motion_count = reader.getf('<H')[0]

                for _ in range(motion_count):
                    motion = OmfMotion()

                    motion.params_offset = reader.offset()
                    motion.name = reader.gets()
                    motion.file = file
                    reader.skip(4 + 2)    # flags, part
                    motion.id_offset = reader.offset()
                    motion_id = reader.getf('<H')[0]
                    omf_file.motions[motion_id] = motion
                    reader.skip(4 * 4)
                    motion.params_end = reader.offset()

            # read motions chunk
            elif chunk_id == ogf.fmt.Chunks_v4.S_MOTIONS_2:
                motions_chunk_offset = reader.offset()
                reader.skip(chunk_size)

            else:
                reader.skip(chunk_size)

        reader.set_offset(motions_chunk_offset)
        chunk_id, chunk_size, motions_count = reader.getf('<3I')
        omf_file.motion_count = motions_count

        for motion_id in range(motions_count):
            chunk_id, chunk_size = reader.getf('<2I')

            motion_offset = reader.offset()
            motion_name = reader.gets()
            length = reader.uint32()

            motion = omf_file.motions[motion_id]
            motion.motion_offset = motion_offset

            for bone_index in range(required_bones_count):
                flags = reader.getf('<B')[0]
                t_present = flags & omf.fmt.FL_T_KEY_PRESENT
                r_absent = flags & omf.fmt.FL_R_KEY_ABSENT
                hq = flags & omf.fmt.KPF_T_HQ

                # skip rotation
                if r_absent:
                    reader.skip(QUAT_16_SZ)
                else:
                    reader.skip(QUAT_16_SZ * length + CRC32_SZ)

                # skip translation
                if t_present:
                    if hq:
                        trn_sz = TRN_16_SZ * length
                    else:
                        trn_sz = TRN_8_SZ * length
                    reader.skip(trn_sz + CRC32_SZ + TRN_INIT_SZ + TRN_SIZE_SZ)
                else:
                    # translate x, y, z float
                    reader.skip(TRN_FLOAT_SZ)

            motion.motion_end = reader.offset()

    # merge params
    params_data = bytearray()

    params_data += omf_parts.data[omf_parts.start : omf_parts.end]

    motion_index = 0
    motions_data = bytearray()
    for omf_file in omf_files:
        for motion_id in range(omf_file.motion_count):
            id_data = struct.pack('<H', motion_index)
            motion = omf_file.motions[motion_id]
            omf_file.data[motion.id_offset : motion.id_offset+2] = id_data
            motion_data = omf_file.data[motion.params_offset : motion.params_end]
            motions_data += motion_data
            motion_index += 1

    motions_count_data = struct.pack('<H', motion_index)

    params_data += motions_count_data + motions_data

    # merge motions
    motions_chunk = bytearray()

    motions_chunk += struct.pack('<3I', 0, 4, motion_index)    # motion count

    for omf_file in omf_files:
        for motion_id in range(omf_file.motion_count):
            motion = omf_file.motions[motion_id]
            motion_data = omf_file.data[motion.motion_offset : motion.motion_end]
            motions_chunk += struct.pack('<2I', motion_id+1, len(motion_data))
            motions_chunk += motion_data

    # merge file data
    file_data = bytearray()

    file_data += struct.pack(
        '<2I',
        ogf.fmt.Chunks_v4.S_MOTIONS_2,
        len(motions_chunk)
    )
    file_data += motions_chunk

    file_data += struct.pack(
        '<2I',
        ogf.fmt.Chunks_v4.S_SMPARAMS_1,
        len(params_data)
    )
    file_data += params_data

    return file_data
