import bpy, mathutils

from . import fmt
from .. import xray_io
from ..version_utils import multiply


MATRIX_BONE = mathutils.Matrix((
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, -1.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0)
)).freeze()
MATRIX_BONE_INVERTED = MATRIX_BONE.inverted().freeze()


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


def read_motion(data, arm_obj, motions_params):
    packed_reader = xray_io.PackedReader(data)
    name = packed_reader.gets()
    length = packed_reader.getf('I')[0]
    motion_params = motions_params[name]

    act = bpy.data.actions.new(name)
    xray_motion = arm_obj.xray.motions_collection.add()
    xray_motion.name = name
    flags = motion_params.flags

    # set flags
    act.xray.flags_fx = bool(flags & fmt.FX)
    act.xray.flags_stopatend = bool(flags & fmt.STOP_AT_END)
    act.xray.flags_nomix = bool(flags & fmt.NO_MIX)
    act.xray.flags_syncpart = bool(flags & fmt.SYNC_PART)
    act.xray.flags_footsteps = bool(flags & fmt.USE_FOOT_STEPS)
    act.xray.flags_movexform = bool(flags & fmt.ROOT_MOVER)
    act.xray.flags_idle = bool(flags & fmt.IDLE)
    act.xray.flags_weaponbone = bool(flags & fmt.USE_WEAPON_BONE)

    act.xray.bonepart = motion_params.bone_or_part
    act.xray.power = motion_params.power
    act.xray.accrue = motion_params.accrue
    act.xray.falloff = motion_params.falloff

    for bone_index, bpy_bone in enumerate(arm_obj.data.bones):
        bone_name = bpy_bone.name
        bpy_bone_parent = bpy_bone.parent

        xmat = bpy_bone.matrix_local.inverted()
        if bpy_bone_parent:
            xmat = multiply(xmat, bpy_bone_parent.matrix_local)
        else:
            xmat = multiply(xmat, MATRIX_BONE)

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

        flags = packed_reader.getf('B')[0]
        t_present = flags & fmt.FL_T_KEY_PRESENT
        r_absent = flags & fmt.FL_R_KEY_ABSENT
        hq = flags & fmt.KPF_T_HQ

        # rotation
        bone_rotations = []
        if r_absent:
            quaternion = packed_reader.getf('4h')
            euler = convert_to_euler(quaternion)
            bone_rotations.append(euler)
        else:
            motion_crc32 = packed_reader.getf('I')[0]
            for key_index in range(length):
                quaternion = packed_reader.getf('4h')
                euler = convert_to_euler(quaternion)
                bone_rotations.append(euler)

        # translation
        bone_translations = []
        translations = []
        if t_present:
            motion_crc32 = packed_reader.getf('I')[0]
            if hq:
                translate_format = '3h'
            else:
                translate_format = '3b'
            for key_index in range(length):
                translate = packed_reader.getf(translate_format)
                translations.append(translate)
            t_size = packed_reader.getf('3f')
            t_init = packed_reader.getf('3f')
            for translate in translations:
                final_translation = [None, None, None]
                for index, component in enumerate(translate):    # x or y or z
                    final_translation[index] = component * t_size[index] + t_init[index]
                final_translation[2] = -final_translation[2]
                bone_translations.append(final_translation)
        else:
            translate = packed_reader.getf('3f')
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

            mat = multiply(
                xmat,
                mathutils.Matrix.Translation(location),
                rotation.to_matrix().to_4x4()
            )
            trn = mat.to_translation()
            rot = mat.to_euler('ZXY')

            if t_present or key_index == 0:
                for i in range(3):
                    translate_fcurves[i].keyframe_points.insert(tr_index, trn[i])

            if not r_absent or key_index == 0:
                for i in range(3):
                    rotate_fcurves[i].keyframe_points.insert(rot_index, rot[i])


def read_motions(data, bpy_armature_obj, motions_params):
    chunked_reader = xray_io.ChunkedReader(data)

    chunk_motion_count_data = chunked_reader.next(fmt.MOTIONS_COUNT_CHUNK)
    motion_count_packed_reader = xray_io.PackedReader(chunk_motion_count_data)
    motions_count = motion_count_packed_reader.getf('I')[0]

    for chunk_id, chunk_data in chunked_reader:
        read_motion(chunk_data, bpy_armature_obj, motions_params)


def read_params(data, bpy_armature_obj, import_bone_parts):
    packed_reader = xray_io.PackedReader(data)

    params_version = packed_reader.getf('H')[0]
    partition_count = packed_reader.getf('H')[0]

    for partition_index in range(partition_count):
        partition_name = packed_reader.gets()
        bone_count = packed_reader.getf('H')[0]
        if import_bone_parts:
            bone_group = bpy_armature_obj.pose.bone_groups.new(name=partition_name)

        for bone in range(bone_count):
            if params_version == 1:
                bone_id = packed_reader.getf('I')[0]
                bone_name = None
            elif params_version == 2:
                bone_id = None
                bone_name = packed_reader.gets()
            elif params_version == 3 or params_version == 4:
                bone_name = packed_reader.gets()
                bone_id = packed_reader.getf('I')[0]
            else:
                raise BaseException('Unknown params version')
            if bone_name:
                pose_bone = bpy_armature_obj.pose.bones[bone_name]
            else:
                pose_bone = bpy_armature_obj.pose.bones[bone_id]
            if import_bone_parts:
                pose_bone.bone_group = bone_group

    motion_count = packed_reader.getf('H')[0]
    motions_params = {}

    for motion_index in range(motion_count):
        motion_params = MotionParams()

        motion_params.name = packed_reader.gets()
        motion_params.flags = packed_reader.getf('I')[0]
        motion_params.bone_or_part = packed_reader.getf('H')[0]
        motion_params.motion = packed_reader.getf('H')[0]
        motion_params.speed = packed_reader.getf('f')[0]
        motion_params.power = packed_reader.getf('f')[0]
        motion_params.accrue = packed_reader.getf('f')[0]
        motion_params.falloff = packed_reader.getf('f')[0]

        motions_params[motion_params.name] = motion_params

        if params_version == 4:
            num_marks = packed_reader.getf('I')[0]
            for mark_index in range(num_marks):
                motion_mark(packed_reader)

    return motions_params


def read_main(data, bpy_armature_obj, import_bone_parts):
    chunked_reader = xray_io.ChunkedReader(data)
    chunks = {}

    for chunk_id, chunk_data in chunked_reader:
        chunks[chunk_id] = chunk_data

    params_chunk_data = chunks.pop(fmt.Chunks.S_SMPARAMS)
    motions_params = read_params(
        params_chunk_data, bpy_armature_obj, import_bone_parts
    )

    motions_chunk_data = chunks.pop(fmt.Chunks.S_MOTIONS)
    read_motions(motions_chunk_data, bpy_armature_obj, motions_params)

    for chunk_id, chunk_data in chunks.items():
        print('Unknown OMF chunk: 0x{:x}', chunk_id)


def import_file(filepath, bpy_armature_obj, import_bone_parts):
    with open(filepath, 'rb') as file:
        data = file.read()
    read_main(data, bpy_armature_obj, import_bone_parts)
