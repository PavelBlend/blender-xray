# standart modules
import struct

# blender modules
import bpy

# addon modules
from . import fmt
from .. import ogf
from ... import ui
from ... import rw
from ... import text
from ... import log


class XRayMergeOmfFile(bpy.types.PropertyGroup):
    file_name = bpy.props.StringProperty()
    file_path = bpy.props.StringProperty()


class XRayMergeOmfProps(bpy.types.PropertyGroup):
    omf_files = bpy.props.CollectionProperty(type=XRayMergeOmfFile)
    omf_index = bpy.props.IntProperty()


class XRAY_UL_merge_omf_list_item(bpy.types.UIList):

    def draw_item(
            self,
            context,
            layout,
            data,
            item,
            icon,
            active_data,
            active_propname
        ):    # pragma: no cover

        layout.row().label(text=item.file_name)


def draw_omf_list_elements(layout):
    layout.operator(
        ui.omf_list.XRAY_OT_remove_all_omfs.bl_idname,
        text='',
        icon='X'
    )


class OmfMotion:
    def __init__(self):
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
        self.motion_count_offset = None


class OmfFile:
    def __init__(self):
        self.file_path = None
        self.data = None
        self.motion_count = None
        self.motions = {}


@log.with_context(name='merge-omf')
def merge_files(files):
    required_params_ver = None
    required_part_count = None
    required_part_names = None
    required_part_bone_names = None
    required_part_bone_ids = None
    required_bones_count = 0

    omf_files = []

    for file_index, file_path in enumerate(files):

        # read file
        with open(file_path, 'rb') as file:
            file_data = bytearray(file.read())

        reader = rw.read.PackedReader(file_data)

        omf_file = OmfFile()
        omf_file.file_path = file_path
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
                    raise log.AppError(
                        text.error.omf_merge_unsupported_params,
                        log.props(file=file_path)
                    )

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
                    # Check boneparts for subsequent files.
                    # Bonepart should be identical to
                    # the bonepart for the first file.

                    if required_params_ver != params_ver:
                        raise log.AppError(
                            text.error.omf_merge_different_params,
                            log.props(file=file_path, version=params_ver)
                        )

                    if required_part_count != parts_count:
                        raise log.AppError(
                            text.error.omf_merge_parts_count,
                            log.props(
                                file=file_path,
                                count=parts_count,
                                must_be=required_part_count
                            )
                        )

                    if required_part_names == part_names:
                        for part_name in required_part_names:
                            req_bone_names = required_part_bone_names[part_name]
                            bone_names = part_bone_names[part_name]

                            if req_bone_names != bone_names:
                                log.warn(
                                    text.warn.omf_merge_part_bone_names,
                                    file=file_path,
                                    part_name=part_name,
                                    bone_names=bone_names,
                                    saved_as=req_bone_names
                                )

                    else:
                        log.warn(
                            text.warn.omf_merge_part_names,
                            file=file_path,
                            parts=part_names,
                            saved_as=required_part_names
                        )

                        for req_name, part_name in zip(required_part_names, part_names):
                            req_bone_names = required_part_bone_names[req_name]
                            bone_names = part_bone_names[part_name]

                            if req_bone_names != bone_names:
                                log.warn(
                                    text.warn.omf_merge_part_bone_names,
                                    file=file_path,
                                    part_name=part_name,
                                    bone_names=bone_names,
                                    saved_as=req_bone_names
                                )

                else:
                    # params for first file
                    required_params_ver = params_ver
                    required_part_count = parts_count
                    required_part_names = part_names
                    required_part_bone_names = part_bone_names
                    required_part_bone_ids = part_bone_ids

                    # bone part for first file
                    omf_parts = OmfParts()
                    omf_parts.data = file_data
                    omf_parts.start = parts_offset
                    omf_parts.end = reader.offset()
                    omf_parts.motion_count_offset = reader.offset()

                # read motions params
                motion_count = reader.getf('<H')[0]

                for _ in range(motion_count):
                    motion = OmfMotion()

                    motion.params_offset = reader.offset()
                    motion.name = reader.gets()
                    reader.skip(4 + 2)    # flags, part
                    motion.id_offset = reader.offset()
                    motion_id = reader.getf('<H')[0]
                    omf_file.motions[motion_id] = motion
                    reader.skip(4 * 4)

                    if params_ver == 4:
                        # skip motion marks
                        num_marks = reader.uint32()
                        for mark_index in range(num_marks):
                            reader.gets_a()    # mark name
                            count = reader.uint32()
                            reader.skip(count * 8)    # intervals

                    motion.params_end = reader.offset()

            # get motions chunk
            elif chunk_id == ogf.fmt.Chunks_v4.S_MOTIONS_2:
                motions_chunk_offset = reader.offset()
                reader.skip(chunk_size)

            else:
                reader.skip(chunk_size)

        # read motions chunk
        reader.set_offset(motions_chunk_offset)

        # read motions count chunk
        chunk_id, chunk_size, motions_count = reader.getf('<3I')
        omf_file.motion_count = motions_count

        # read motions
        for motion_id in range(motions_count):
            chunk_id, chunk_size = reader.getf('<2I')

            motion_offset = reader.offset()
            motion_name = reader.gets()
            length = reader.uint32()

            motion = omf_file.motions[motion_id]
            motion.motion_offset = motion_offset

            for bone_index in range(required_bones_count):
                flags = reader.getf('<B')[0]
                t_present = flags & fmt.FL_T_KEY_PRESENT
                r_absent = flags & fmt.FL_R_KEY_ABSENT
                hq = flags & fmt.KPF_T_HQ

                # skip rotation
                if r_absent:
                    reader.skip(fmt.QUAT_16_SZ)
                else:
                    reader.skip(fmt.QUAT_16_SZ * length + fmt.CRC32_SZ)

                # skip translation
                if t_present:
                    if hq:
                        trn_sz = fmt.TRN_16_SZ * length
                    else:
                        trn_sz = fmt.TRN_8_SZ * length
                    reader.skip(trn_sz + fmt.CRC32_SZ + fmt.TRN_INIT_SZ + fmt.TRN_SIZE_SZ)
                else:
                    # translate x, y, z float
                    reader.skip(fmt.TRN_FLOAT_SZ)

            motion.motion_end = reader.offset()

    # merge motions
    motions_chunks = bytearray()

    saved_motions = set()
    motions_params = []
    motion_chunk_id = 1

    for omf_file in omf_files:
        for motion_id in range(omf_file.motion_count):
            motion = omf_file.motions[motion_id]

            if motion.name in saved_motions:
                log.warn(
                    text.warn.omf_merge_motion_duplicate,
                    file=omf_file.file_path,
                    motion=motion.name
                )
                continue

            saved_motions.add(motion.name)
            motions_params.append((omf_file, motion))

            # get motion data
            data = omf_file.data[motion.motion_offset : motion.motion_end]

            # write motion chunk
            chunk_size = len(data)
            motions_chunks += struct.pack('<2I', motion_chunk_id, chunk_size)
            motions_chunks += data
            motion_chunk_id += 1

    # write motions count chunk
    motions_count_chunk = struct.pack(
        '<3I',
        fmt.MOTIONS_COUNT_CHUNK,    # chunk id
        4,    # chunk size
        motion_chunk_id - 1    # motion count
    )
    motions_chunk = motions_count_chunk + motions_chunks

    # merge params
    params_data = bytearray()

    # merge bone parts
    params_data += omf_parts.data[omf_parts.start : omf_parts.end]

    # merge motions params
    motion_index = 0
    motions_param_data = bytearray()

    for omf_file, motion in motions_params:
        # replace motion id
        id_data = struct.pack('<H', motion_index)
        omf_file.data[motion.id_offset : motion.id_offset + 2] = id_data

        # append motion params
        params = omf_file.data[motion.params_offset : motion.params_end]
        motions_param_data += params

        motion_index += 1

    # write motions count
    motions_count_data = struct.pack('<H', motion_chunk_id - 1)

    # write motions params
    params_data += motions_count_data + motions_param_data

    # write file data
    file_data = bytearray()

    # write motions chunk
    file_data += struct.pack(
        '<2I',
        ogf.fmt.Chunks_v4.S_MOTIONS_2,
        len(motions_chunk)
    )
    file_data += motions_chunk

    # write params chunk
    file_data += struct.pack(
        '<2I',
        ogf.fmt.Chunks_v4.S_SMPARAMS_1,
        len(params_data)
    )
    file_data += params_data

    return file_data
