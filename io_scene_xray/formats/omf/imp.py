# blender modules
import bpy
import mathutils

# addon modules
from . import fmt
from .. import ogf
from .. import motions
from ... import text
from ... import log
from ... import utils
from ... import rw


def read_motion_marks(packed_reader):
    num_marks = packed_reader.uint32()

    for mark_index in range(num_marks):
        name = packed_reader.gets_a()
        count = packed_reader.uint32()

        for index in range(count):
            interval_first, interval_second = packed_reader.getf('<2f')


def examine_motions(data):
    motion_names = []
    chunked_reader = rw.read.ChunkedReader(data)

    # size of motion flags, part, id, speed, power, accrue, falloff
    params_size = 4 + 2 + 2 + 4 + 4 + 4 + 4

    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == ogf.fmt.Chunks_v4.S_SMPARAMS_1:
            packed_reader = rw.read.PackedReader(chunk_data)

            # bone partitions
            params_ver, parts_count = packed_reader.getf('<2H')

            for partition_index in range(parts_count):
                packed_reader.gets()    # partition name
                bone_count = packed_reader.getf('<H')[0]

                for bone in range(bone_count):
                    if params_ver in (3, 4):
                        packed_reader.gets()    # bone name
                        packed_reader.skip(4)    # bone id

                    elif params_ver == 2:
                        packed_reader.gets()    # bone name

                    else:    # version 1
                        packed_reader.skip(4)    # bone id

            # motion params
            motion_count = packed_reader.getf('<H')[0]

            for motion_index in range(motion_count):
                motion_name = packed_reader.gets()
                packed_reader.skip(params_size)

                if params_ver == 4:
                    num_marks = packed_reader.uint32()
                    for mark_index in range(num_marks):
                        packed_reader.gets_a()    # mark name
                        count = packed_reader.uint32()
                        packed_reader.skip(count * 8)    # intervals

                motion_names.append(motion_name)

    return motion_names


class MotionParams:
    def __init__(self):
        self.name = None
        self.flags = None
        self.bone_or_part = None
        self.motion = None
        self.speed = None
        self.power = None
        self.accrue = None
        self.falloff = None


def quat_to_euler(quaternion):
    return mathutils.Quaternion((
        quaternion[3] / 0x7fff,
        quaternion[0] / 0x7fff,
        quaternion[1] / 0x7fff,
        -quaternion[2] / 0x7fff
    )).to_euler('ZXY')


# data size
CRC32_SZ = 4
QUAT_16_SZ = 4 * 2    # x, y, z, w 16 bit
TRN_8_SZ = 3 * 1    # x, y, z 8 bit
TRN_16_SZ = 3 * 2    # x, y, z 16 bit
TRN_FLOAT_SZ = 3 * 4    # x, y, z float
TRN_INIT_SZ = 3 * 4    # x, y, z float
TRN_SIZE_SZ = 3 * 4    # x, y, z float


def skip_motion(packed_reader, bone_names):
    for bone_index in range(len(bone_names)):
        flags = packed_reader.getf('<B')[0]
        t_present = flags & fmt.FL_T_KEY_PRESENT
        r_absent = flags & fmt.FL_R_KEY_ABSENT
        hq = flags & fmt.KPF_T_HQ

        # skip rotation
        if r_absent:
            packed_reader.skip(QUAT_16_SZ)
        else:
            packed_reader.skip(QUAT_16_SZ * length + CRC32_SZ)

        # skip translation
        if t_present:
            if hq:
                trn_sz = TRN_16_SZ * length
            else:
                trn_sz = TRN_8_SZ * length
            packed_reader.skip(trn_sz + CRC32_SZ + TRN_INIT_SZ + TRN_SIZE_SZ)
        else:
            # translate x, y, z float
            packed_reader.skip(TRN_FLOAT_SZ)


def read_motion(data, context, motions_params, bone_names, version):
    packed_reader = rw.read.PackedReader(data)
    name = packed_reader.gets()
    length = packed_reader.uint32()

    import_motion = False
    if context.selected_names is None:
        import_motion = True
    else:
        if name in context.selected_names:
            import_motion = True

    if import_motion:
        act = bpy.data.actions.new(name)
        utils.stats.created_act()
        act.use_fake_user = True
        if context.add_to_motion_list:
            xray_motion = context.bpy_arm_obj.xray.motions_collection.add()
            xray_motion.name = name
            if xray_motion.name != act.name:
                xray_motion.name = act.name
                xray_motion.export_name = name
                context.bpy_arm_obj.xray.use_custom_motion_names = True

        motion_params = motions_params[name]

        act.xray.flags = motion_params.flags
        act.xray.bonepart = motion_params.bone_or_part
        act.xray.power = motion_params.power
        act.xray.accrue = motion_params.accrue
        act.xray.speed = motion_params.speed
        act.xray.falloff = motion_params.falloff

        cannot_find_bones = set()
        bones_count = len(bone_names)
        for bone_index in range(bones_count):
            bone_name = bone_names.get(bone_index, None)
            if bone_name is None:
                bone_name = context.bpy_arm_obj.data.bones.keys()[bone_index]
            bpy_bone = context.bpy_arm_obj.data.bones.get(bone_name)
            if bpy_bone:
                bone_name = bpy_bone.name
            else:
                cannot_find_bones.add((bone_name, bone_index))
                continue
            bpy_bone_parent = bpy_bone.parent

            xmat = bpy_bone.matrix_local.inverted()
            if bpy_bone_parent:
                xmat = context.multiply(xmat, bpy_bone_parent.matrix_local)
            else:
                xmat = context.multiply(xmat, motions.const.MATRIX_BONE)

            translate_fcurves = []
            for translate_index in range(3):    # x, y, z
                translate_fcurve = act.fcurves.new(
                    'pose.bones["{}"].location'.format(bone_name),
                    index=translate_index,
                    action_group=bone_name
                )
                translate_fcurves.append(translate_fcurve)

            rotate_fcurves = []
            for rotate_index in range(3):    # x, y, z
                rotate_fcurve = act.fcurves.new(
                    'pose.bones["{}"].rotation_euler'.format(bone_name),
                    index=rotate_index,
                    action_group=bone_name
                )
                rotate_fcurves.append(rotate_fcurve)

            bone_rotations = []
            bone_translations = []

            if version == 2:
                flags = packed_reader.getf('<B')[0]
                t_present = flags & fmt.FL_T_KEY_PRESENT
                r_absent = flags & fmt.FL_R_KEY_ABSENT
                hq = flags & fmt.KPF_T_HQ

            elif version == 1:
                t_present = packed_reader.getf('<B')[0]
                r_absent = False
                hq = False

            elif version == 0:
                frame_len = 4 * 2 + 3 * 4    # quaternion: 4H, translate: 3f
                head_len = len(name) + 1 + 4
                if len(packed_reader.get_size()) - head_len == length * bones_count * frame_len:
                    quat_fmt = 'h'
                else:
                    quat_fmt = 'f'
                for bone_index in range(bones_count):
                    for key_index in range(length):
                        quat = packed_reader.getf('<4' + quat_fmt)
                        loc = packed_reader.getf('<3f')

                        euler = mathutils.Quaternion((
                            quat[3],
                            quat[0],
                            quat[1],
                            -quat[2]
                        )).to_euler('ZXY')
                        bone_rotations.append(euler)

                        translate = loc[0], loc[1], -loc[2]
                        bone_translations.append(translate)

            if version != 0:
                # rotation
                if r_absent:
                    quaternion = packed_reader.getf('<4h')
                    euler = quat_to_euler(quaternion)
                    bone_rotations.append(euler)
                else:
                    motion_crc32 = packed_reader.uint32()
                    for key_index in range(length):
                        quaternion = packed_reader.getf('<4h')
                        euler = quat_to_euler(quaternion)
                        bone_rotations.append(euler)

                # translation
                translations = []
                if t_present:
                    motion_crc32 = packed_reader.uint32()
                    if hq:
                        translate_format = '3h'
                    else:
                        translate_format = '3b'
                    for key_index in range(length):
                        translate = packed_reader.getf('<' + translate_format)
                        translations.append(translate)
                    t_size = packed_reader.getf('<3f')
                    t_init = packed_reader.getf('<3f')
                    for translate in translations:
                        final_translation = [None, None, None]
                        for index, component in enumerate(translate):    # x or y or z
                            final_translation[index] = component * t_size[index] + t_init[index]
                        final_translation[2] = -final_translation[2]
                        bone_translations.append(final_translation)
                else:
                    translate = packed_reader.getf('<3f')
                    translate = translate[0], translate[1], -translate[2]
                    bone_translations.append(translate)

            tr_count = len(bone_translations)
            rot_count = len(bone_rotations)
            keys_count = max(tr_count, rot_count)
            frames_coords = [[], [], [], [], [], []]

            for key_index in range(keys_count):
                if t_present:
                    tr_index = key_index
                else:
                    tr_index = 0
                if not r_absent:
                    rot_index = key_index
                else:
                    rot_index = 0

                location = bone_translations[tr_index]
                rotation = bone_rotations[rot_index]

                mat = context.multiply(
                    xmat,
                    mathutils.Matrix.Translation(location),
                    rotation.to_matrix().to_4x4()
                )
                trn = mat.to_translation()
                rot = mat.to_euler('ZXY')

                if t_present or key_index == 0:
                    for axis in range(3):
                        frames_coords[axis].extend((tr_index, trn[axis]))

                if not r_absent or key_index == 0:
                    for axis in range(3):
                        frames_coords[axis + 3].extend((rot_index, rot[axis]))

            # insert keyframes
            fcurves = [*translate_fcurves, *rotate_fcurves]
            utils.action.insert_keyframes(frames_coords, fcurves)

        if cannot_find_bones:
            raise log.AppError(
                text.error.omf_no_bone,
                log.props(
                    armature_object=context.bpy_arm_obj.name,
                    bone_names_and_indices=cannot_find_bones
                )
            )

    else:
        skip_motion(packed_reader, bone_names)


def read_motions(data, context, motions_params, bone_names, version=2):
    chunked_reader = rw.read.ChunkedReader(data)

    count_data = chunked_reader.next(fmt.MOTIONS_COUNT_CHUNK)
    count_reader = rw.read.PackedReader(count_data)
    motions_count = count_reader.uint32()

    for chunk_id, chunk_data in chunked_reader:
        read_motion(chunk_data, context, motions_params, bone_names, version)


def read_params(data, context, chunk, bones_indices={}):
    reader = rw.read.PackedReader(data)

    if chunk == 1:
        params_version = reader.getf('<H')[0]

        if not params_version in (1, 2, 3, 4):
            raise 'unsupported motion params version: ' + str(params_version)

    else:
        params_version = 0

    # read bone parts
    partition_count = reader.getf('<H')[0]
    bone_names = {}
    cannot_find_bones = set()
    pose = context.bpy_arm_obj.pose

    for partition_index in range(partition_count):
        partition_name = reader.gets()
        bone_count = reader.getf('<H')[0]

        # create bone group
        if context.import_bone_parts:
            bone_group = pose.bone_groups.get(partition_name)
            if not bone_group:
                bone_group = pose.bone_groups.new(name=partition_name)

        for bone in range(bone_count):
            if params_version in (3, 4):
                bone_name = reader.gets()
                bone_id = reader.uint32()
                bone_names[bone_id] = bone_name

            elif params_version == 2:
                bone_id = bone
                bone_name = reader.gets()
                bone_names[bone_id] = bone_name

            else:    # versions 0, 1
                bone_id = reader.uint32()
                bone_name = bones_indices.get(bone_id, None)
                bone_names[bone_id] = bone_name

            if bone_name:
                pose_bone = pose.bones.get(bone_name, None)
                if not pose_bone:
                    cannot_find_bones.add((bone_name, bone))
                    continue
            else:
                pose_bone = pose.bones[bone_id]

            if context.import_bone_parts:
                pose_bone.bone_group = bone_group

    if cannot_find_bones:
        raise log.AppError(
            text.error.omf_no_bone,
            log.props(
                armature_object=context.bpy_arm_obj.name,
                bone_names_and_indices=cannot_find_bones
            )
        )

    # read motions params
    motion_count = reader.getf('<H')[0]
    motions_params = {}

    for motion_index in range(motion_count):
        motion_name = reader.gets()
        prm = MotionParams()
        motions_params[motion_name] = prm

        prm.flags = reader.uint32()
        prm.bone_or_part, prm.motion = reader.getf('<2H')
        prm.speed, prm.power, prm.accrue, prm.falloff = reader.getf('<4f')

        if params_version == 4:
            read_motion_marks(reader)

        elif params_version == 0:
            b_no_loop = reader.getf('<B')[0]

    return motions_params, bone_names


def read_main(data, context):
    if not context.import_motions and not context.import_bone_parts:
        raise log.AppError(text.error.omf_nothing)

    chunks = rw.utils.get_chunks(data)

    # params
    params_data = chunks.pop(ogf.fmt.Chunks_v4.S_SMPARAMS_1)
    params_chunk = 1
    motions_params, bone_names = read_params(
        params_data,
        context,
        params_chunk
    )

    # motions
    motions_data = chunks.pop(ogf.fmt.Chunks_v4.S_MOTIONS_2)
    if context.import_motions:
        read_motions(motions_data, context, motions_params, bone_names)

    for chunk_id, chunk_data in chunks.items():
        print('Unknown OMF chunk: 0x{:x}'.format(chunk_id))


@log.with_context(name='import-omf')
@utils.stats.timer
def import_file(context):
    utils.stats.status('Import File', context.filepath)
    file_data = rw.utils.get_file_data(context.filepath)
    read_main(file_data, context)
