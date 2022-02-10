# blender modules
import bpy
import mathutils

# addon modules
from . import fmt
from .. import text
from .. import log
from .. import xray_io
from .. import utils
from .. import ie_utils


MATRIX_BONE = mathutils.Matrix((
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, -1.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0)
)).freeze()
MATRIX_BONE_INVERTED = MATRIX_BONE.inverted().freeze()


def motion_mark(packed_reader):
    name = packed_reader.gets_a()
    count = packed_reader.getf('<I')[0]
    for index in range(count):
        interval_first = packed_reader.getf('<f')[0]
        interval_second = packed_reader.getf('<f')[0]


def examine_motions(data):
    motion_names = []
    chunked_reader = xray_io.ChunkedReader(data)
    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == fmt.Chunks.S_SMPARAMS:
            packed_reader = xray_io.PackedReader(chunk_data)
            params_version = packed_reader.getf('<H')[0]
            partition_count = packed_reader.getf('<H')[0]
            for partition_index in range(partition_count):
                partition_name = packed_reader.gets()
                bone_count = packed_reader.getf('<H')[0]
                for bone in range(bone_count):
                    if params_version == 1:
                        bone_id = packed_reader.getf('<I')[0]
                        bone_name = None
                    elif params_version == 2:
                        bone_id = None
                        bone_name = packed_reader.gets()
                    elif params_version in (3, 4):
                        bone_name = packed_reader.gets()
                        bone_id = packed_reader.getf('<I')[0]
                    else:
                        raise BaseException('Unknown params version')
            motion_count = packed_reader.getf('<H')[0]
            for motion_index in range(motion_count):
                name = packed_reader.gets()
                motion_names.append(name)
                flags = packed_reader.getf('<I')[0]
                bone_or_part = packed_reader.getf('<H')[0]
                motion = packed_reader.getf('<H')[0]
                speed = packed_reader.getf('<f')[0]
                power = packed_reader.getf('<f')[0]
                accrue = packed_reader.getf('<f')[0]
                falloff = packed_reader.getf('<f')[0]
                if params_version == 4:
                    num_marks = packed_reader.getf('<I')[0]
                    for mark_index in range(num_marks):
                        motion_mark(packed_reader)
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


def convert_to_euler(quaternion):
    euler = mathutils.Quaternion((
        quaternion[3] / 0x7fff,
        quaternion[0] / 0x7fff,
        quaternion[1] / 0x7fff,
        -quaternion[2] / 0x7fff
    )).to_euler('ZXY')
    return euler


def read_motion(data, context, motions_params, bone_names):
    packed_reader = xray_io.PackedReader(data)
    name = packed_reader.gets()
    length = packed_reader.getf('<I')[0]
    motion_params = motions_params[name]

    import_motion = False
    if not context.selected_names is None:
        if name in context.selected_names:
            import_motion = True
    else:
        import_motion = True

    if import_motion:
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        if context.add_actions_to_motion_list:
            xray_motion = context.bpy_arm_obj.xray.motions_collection.add()
            xray_motion.name = name
            if xray_motion.name != act.name:
                xray_motion.name = act.name
                xray_motion.export_name = name
                context.bpy_arm_obj.xray.use_custom_motion_names = True

        act.xray.flags = motion_params.flags
        act.xray.bonepart = motion_params.bone_or_part
        act.xray.power = motion_params.power
        act.xray.accrue = motion_params.accrue
        act.xray.speed = motion_params.speed
        act.xray.falloff = motion_params.falloff

        cannot_find_bones = set()
        for bone_index in range(len(bone_names)):
            bone_name = bone_names.get(bone_index, None)
            if bone_name is None:
                bpy_bone = context.bpy_arm_obj.data.bones.get(bone_index)
            else:
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
                xmat = context.multiply(xmat, MATRIX_BONE)

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

            flags = packed_reader.getf('<B')[0]
            t_present = flags & fmt.FL_T_KEY_PRESENT
            r_absent = flags & fmt.FL_R_KEY_ABSENT
            hq = flags & fmt.KPF_T_HQ

            # rotation
            bone_rotations = []
            if r_absent:
                quaternion = packed_reader.getf('<4h')
                euler = convert_to_euler(quaternion)
                bone_rotations.append(euler)
            else:
                motion_crc32 = packed_reader.getf('<I')[0]
                for key_index in range(length):
                    quaternion = packed_reader.getf('<4h')
                    euler = convert_to_euler(quaternion)
                    bone_rotations.append(euler)

            # translation
            bone_translations = []
            translations = []
            if t_present:
                motion_crc32 = packed_reader.getf('<I')[0]
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
                        translate_fcurves[axis].keyframe_points.insert(tr_index, trn[axis])

                if not r_absent or key_index == 0:
                    for axis in range(3):
                        rotate_fcurves[axis].keyframe_points.insert(rot_index, rot[axis])

        if cannot_find_bones:
            raise utils.AppError(
                text.error.omf_no_bone,
                log.props(
                    armature_object=context.bpy_arm_obj.name,
                    bone_names_and_indices=cannot_find_bones
                )
            )

    else:
        for bone_index in range(len(bone_names)):
            flags = packed_reader.getf('<B')[0]
            t_present = flags & fmt.FL_T_KEY_PRESENT
            r_absent = flags & fmt.FL_R_KEY_ABSENT
            hq = flags & fmt.KPF_T_HQ
            if r_absent:
                # quaternion
                packed_reader.skip(4 * 2)
            else:
                # quaternions + motion_crc32
                packed_reader.skip(4 * 2 * length + 4)
            if t_present:
                if hq:
                    translate_size = 3 * 2
                else:
                    translate_size = 3 * 1
                packed_reader.skip(length * translate_size + 4 + 12 + 12)
            else:
                packed_reader.skip(12)


def read_motions(data, context, motions_params, bone_names):
    chunked_reader = xray_io.ChunkedReader(data)

    chunk_motion_count_data = chunked_reader.next(fmt.MOTIONS_COUNT_CHUNK)
    motion_count_packed_reader = xray_io.PackedReader(chunk_motion_count_data)
    motions_count = motion_count_packed_reader.getf('<I')[0]

    for chunk_id, chunk_data in chunked_reader:
        read_motion(chunk_data, context, motions_params, bone_names)


def read_params(data, context):
    packed_reader = xray_io.PackedReader(data)

    params_version = packed_reader.getf('<H')[0]
    partition_count = packed_reader.getf('<H')[0]
    bone_names = {}
    cannot_find_bones = set()
    pose = context.bpy_arm_obj.pose

    for partition_index in range(partition_count):
        partition_name = packed_reader.gets()
        bone_count = packed_reader.getf('<H')[0]
        if context.import_bone_parts:
            bone_group = pose.bone_groups.get(partition_name)
            if not bone_group:
                bone_group = pose.bone_groups.new(name=partition_name)

        for bone in range(bone_count):
            if params_version == 1:
                bone_id = packed_reader.getf('<I')[0]
                bone_name = None
                bone_names[bone_id] = None
            elif params_version == 2:
                bone_id = None
                bone_name = packed_reader.gets()
                bone_names[bone] = bone_name
            elif params_version == 3 or params_version == 4:
                bone_name = packed_reader.gets()
                bone_id = packed_reader.getf('<I')[0]
                bone_names[bone_id] = bone_name
            else:
                raise BaseException('Unknown params version')
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
        raise utils.AppError(
            text.error.omf_no_bone,
            log.props(
                armature_object=context.bpy_arm_obj.name,
                bone_names_and_indices=cannot_find_bones
            )
        )

    motion_count = packed_reader.getf('<H')[0]
    motions_params = {}

    for motion_index in range(motion_count):
        motion_params = MotionParams()

        motion_params.name = packed_reader.gets()
        motion_params.flags = packed_reader.getf('<I')[0]
        motion_params.bone_or_part = packed_reader.getf('<H')[0]
        motion_params.motion = packed_reader.getf('<H')[0]
        motion_params.speed = packed_reader.getf('<f')[0]
        motion_params.power = packed_reader.getf('<f')[0]
        motion_params.accrue = packed_reader.getf('<f')[0]
        motion_params.falloff = packed_reader.getf('<f')[0]

        motions_params[motion_params.name] = motion_params

        if params_version == 4:
            num_marks = packed_reader.getf('<I')[0]
            for mark_index in range(num_marks):
                motion_mark(packed_reader)

    return motions_params, bone_names


def read_main(data, context):
    if not context.import_motions and not context.import_bone_parts:
        raise utils.AppError(text.error.omf_nothing)
        return

    chunked_reader = xray_io.ChunkedReader(data)
    chunks = {}

    for chunk_id, chunk_data in chunked_reader:
        chunks[chunk_id] = chunk_data

    params_chunk_data = chunks.pop(fmt.Chunks.S_SMPARAMS)
    motions_params, bone_names = read_params(params_chunk_data, context)
    del params_chunk_data

    if context.import_motions:
        motions_chunk_data = chunks.pop(fmt.Chunks.S_MOTIONS)
        read_motions(motions_chunk_data, context, motions_params, bone_names)
        del motions_chunk_data

    for chunk_id, chunk_data in chunks.items():
        print('Unknown OMF chunk: 0x{:x}'.format(chunk_id))


@log.with_context(name='file')
def import_file(context):
    log.update(path=context.filepath)
    ie_utils.check_file_exists(context.filepath)
    file_data = utils.read_file(context.filepath)
    read_main(file_data, context)
