# standart modules
import struct
import zlib

# blender modules
import bpy
import mathutils

# addon modules
from . import fmt
from . import imp
from .. import text
from .. import log
from .. import xray_io
from .. import utils


def get_flags(xray):
    flags = 0x0
    if xray.flags_fx:
        flags |= fmt.FX
    if xray.flags_stopatend:
        flags |= fmt.STOP_AT_END
    if xray.flags_nomix:
        flags |= fmt.NO_MIX
    if xray.flags_syncpart:
        flags |= fmt.SYNC_PART
    if xray.flags_footsteps:
        flags |= fmt.USE_FOOT_STEPS
    if xray.flags_movexform:
        flags |= fmt.ROOT_MOVER
    if xray.flags_idle:
        flags |= fmt.IDLE
    if xray.flags_weaponbone:
        flags |= fmt.USE_WEAPON_BONE
    return flags


def validate_omf_file(context):
    data = utils.read_file(context.filepath)
    if not len(data):
        raise utils.AppError(
            text.error.omf_empty,
            log.props(file=context.filepath)
        )
    chunked_reader = xray_io.ChunkedReader(data)
    chunks = {}
    for chunk_id, chunk_data in chunked_reader:
        chunks[chunk_id] = chunk_data
    chunks_ids = list(chunks.keys())
    if not fmt.Chunks.S_MOTIONS in chunks_ids and context.export_motions:
        raise utils.AppError(
            text.error.omf_no_anims,
            log.props(file=context.filepath)
        )
    if not fmt.Chunks.S_SMPARAMS in chunks_ids and context.export_bone_parts:
        raise utils.AppError(
            text.error.omf_no_params,
            log.props(file=context.filepath)
        )
    return data, chunks


def get_exclude_motion_names(context):
    data, chunks = validate_omf_file(context)
    motion_names = imp.examine_motions(data)
    return set(motion_names), chunks


class BonePart:
    def __init__(self):
        self.bones = []
        self.name = None
        self.bones_count = None


class Bone:
    def __init__(self):
        self.name = None
        self.index = None


class BoneParts:
    def __init__(self):
        self.version = None
        self.count = None
        self.items = []


class Motion:
    def __init__(self):
        self.name = None
        self.writer = xray_io.PackedWriter()


def get_motion_params(data):
    packed_reader = xray_io.PackedReader(data)
    bone_parts = BoneParts()
    bone_parts.version = packed_reader.getf('<H')[0]
    bone_parts.count = packed_reader.getf('<H')[0]
    for partition_index in range(bone_parts.count):
        bonepart = BonePart()
        bonepart.name = packed_reader.gets()
        bonepart.bones_count = packed_reader.getf('<H')[0]
        for bone_index in range(bonepart.bones_count):
            bone = Bone()
            if bone_parts.version == 1:
                bone.index = packed_reader.getf('<I')[0]
            elif bone_parts.version == 2:
                bone.name = packed_reader.gets()
            elif bone_parts.version in (3, 4):
                bone.name = packed_reader.gets()
                bone.index = packed_reader.getf('<I')[0]
            else:
                raise BaseException('Unknown params version')
            bonepart.bones.append(bone)
        bone_parts.items.append(bonepart)
    motions_params = {}
    motion_count = packed_reader.getf('<H')[0]
    for motion_index in range(motion_count):
        motion = Motion()
        motion.name = packed_reader.gets()
        motion.writer.data.extend(packed_reader.getb(24))
        if bone_parts.version == 4:
            num_marks = packed_reader.getf('<I')[0]
            motion.writer.data.extend(struct.pack('<I', num_marks))
            for mark_index in range(num_marks):
                mark_name = packed_reader.gets_a()
                mark_count = packed_reader.getf('<I')[0]
                mark_name = bytes(mark_name, 'cp1251')
                motion.writer.data.extend(struct.pack(
                    '<{}s'.format(len(mark_name)),
                    mark_name
                ))
                motion.writer.data.append(0xa)    # end string
                motion.writer.data.extend(struct.pack('<I', mark_count))
                motion.writer.data.extend(packed_reader.getb(8 * mark_count))
        motions_params[motion.name] = motion
    return bone_parts, motions_params


def get_motions(context):
    _, chunks = validate_omf_file(context)
    chunked_reader = xray_io.ChunkedReader(chunks[fmt.Chunks.S_MOTIONS])
    motions = {}
    chunked_reader.next(fmt.MOTIONS_COUNT_CHUNK)
    motion_names = []
    for chunk_id, chunk_data in chunked_reader:
        packed_reader = xray_io.PackedReader(chunk_data)
        packed_writer = xray_io.PackedWriter()
        name = packed_reader.gets()
        motion_names.append(name)
        packed_writer.puts(name)
        length = packed_reader.getf('<I')[0]
        packed_writer.putf('I', length)
        for bone_index in range(len(context.bpy_arm_obj.data.bones)):
            flags = packed_reader.getf('<B')[0]
            t_present = flags & fmt.FL_T_KEY_PRESENT
            r_absent = flags & fmt.FL_R_KEY_ABSENT
            hq = flags & fmt.KPF_T_HQ
            packed_writer.putf('<B', flags)
            if r_absent:
                quaternion = packed_reader.getf('<4h')
                packed_writer.putf('<4h', *quaternion)
            else:
                motion_crc32 = packed_reader.getf('<I')[0]
                packed_writer.putf('<I', motion_crc32)
                for key_index in range(length):
                    quaternion = packed_reader.getf('<4h')
                    packed_writer.putf('<4h', *quaternion)
            if t_present:
                motion_crc32 = packed_reader.getf('<I')[0]
                packed_writer.putf('<I', motion_crc32)
                if hq:
                    translate_format = '3h'
                else:
                    translate_format = '3b'
                for key_index in range(length):
                    translate = packed_reader.getf('<' + translate_format)
                    packed_writer.putf(translate_format, *translate)
                t_size = packed_reader.getf('<3f')
                packed_writer.putf('<3f', *t_size)
                t_init = packed_reader.getf('<3f')
                packed_writer.putf('<3f', *t_init)
            else:
                translate = packed_reader.getf('<3f')
                packed_writer.putf('<3f', *translate)
        motions[name] = (packed_writer, chunk_id)
    return motions, motion_names, chunks


def write_motion(context, packed_writer, motion_name, motion_index, params_version):
    action = bpy.data.actions.get(motion_name)
    if context.bpy_arm_obj.xray.use_custom_motion_names:
        motion_name = context.motion_export_names[motion_name]
    packed_writer.puts(motion_name)
    motion_flags = get_flags(action.xray)
    packed_writer.putf('<I', motion_flags)
    bone_or_part = action.xray.bonepart
    packed_writer.putf('<H', bone_or_part)
    packed_writer.putf('<H', motion_index)
    packed_writer.putf('<f', action.xray.speed)
    packed_writer.putf('<f', action.xray.power)
    packed_writer.putf('<f', action.xray.accrue)
    packed_writer.putf('<f', action.xray.falloff)
    if params_version == 4:
        packed_writer.putf('<I', 0)    # marks count


def write_motions(context, packed_writer, motions, version):
    for motion_name, motion_index, _ in motions:
        write_motion(context, packed_writer, motion_name, motion_index, version)


@log.with_context('armature-object')
def export_omf(context):
    log.update(object=context.bpy_arm_obj.name)
    current_frame = bpy.context.scene.frame_current
    mode = context.bpy_arm_obj.mode
    if not context.bpy_arm_obj.animation_data:
        current_action = None
    else:
        current_action = context.bpy_arm_obj.animation_data.action
    motion_names = set()
    context.motion_export_names = {}
    for motion in context.bpy_arm_obj.xray.motions_collection:
        motion_names.add(motion.name)
        if motion.export_name:
            context.motion_export_names[motion.name] = motion.export_name
        else:
            context.motion_export_names[motion.name] = motion.name
    if context.export_mode in ('ADD', 'REPLACE'):
        available_motions, available_motion_names, chunks = get_motions(context)
        available_motion_names.extend(
            list(motion_names - set(available_motion_names))
        )
        export_motion_names = available_motion_names
    else:
        available_motions = {}
        export_motion_names = list(motion_names)
    scn = bpy.context.scene
    pose_bones = []
    utils.set_mode('POSE')
    bone_groups = {}
    no_group_bones = set()
    for bone_index, bone in enumerate(context.bpy_arm_obj.data.bones):
        if bone.xray.exportable:
            pose_bone = context.bpy_arm_obj.pose.bones[bone.name]
            pose_bones.append(pose_bone)
            if not pose_bone.bone_group:
                if context.need_bone_groups:
                    no_group_bones.add(pose_bone.name)
                    continue
                else:
                    continue
            bone_groups.setdefault(pose_bone.bone_group.name, []).append(
                (pose_bone.name, bone_index)
            )
    if no_group_bones:
        raise utils.AppError(
            text.error.omf_bone_no_group,
            log.props(
                armature_object=context.bpy_arm_obj.name,
                bones=no_group_bones
            )
        )
    motion_count = 0
    motions = []
    motions_ids = {}
    if context.export_mode == 'OVERWRITE':
        for motion_name in export_motion_names:
            action = bpy.data.actions.get(motion_name)
            if not action:
                continue
            motions.append((motion_name, motion_count, False))
            motions_ids[motion_name] = motion_count
            motion_count += 1
    else:
        for motion_name in export_motion_names:
            action = bpy.data.actions.get(motion_name)
            _, motion_id = available_motions.get(motion_name, (None, None))
            if not action:
                if motion_id is None:
                    continue
            if not motion_id is None:
                motions.append((motion_name, motion_id, True))
            else:
                motions.append((motion_name, motion_count, False))
            motions_ids[motion_name] = motion_count
            motion_count += 1
    chunked_writer = xray_io.ChunkedWriter()
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', motion_count)
    chunked_writer.put(fmt.MOTIONS_COUNT_CHUNK, packed_writer)
    chunk_id = fmt.MOTIONS_COUNT_CHUNK + 1
    context.bpy_arm_obj.animation_data_create()
    new_motions_count = 0
    xray = context.bpy_arm_obj.xray
    dependency_object = None
    if xray.dependency_object:
        dependency_object = bpy.data.objects.get(xray.dependency_object)
        if dependency_object:
            dep_action = dependency_object.animation_data.action
    for motion_name in export_motion_names:
        action = bpy.data.actions.get(motion_name)
        packed_writer, _ = available_motions.get(motion_name, (None, None))
        if context.export_mode == 'ADD' and not packed_writer is None:
            chunked_writer.put(chunk_id, packed_writer)
            chunk_id += 1
            continue
        if context.export_mode == 'REPLACE':
            if not motion_name in motion_names and packed_writer:
                chunked_writer.put(chunk_id, packed_writer)
                chunk_id += 1
                continue
        if not action:
            if context.export_mode == 'REPLACE':
                if packed_writer is None:
                    continue
                else:
                    chunked_writer.put(chunk_id, packed_writer)
                    chunk_id += 1
                    continue
            else:
                continue
        if context.export_mode == 'ADD':
            new_motions_count += 1
        elif context.export_mode == 'REPLACE':
            if packed_writer is None:
                new_motions_count += 1
        packed_writer = xray_io.PackedWriter()
        context.bpy_arm_obj.animation_data.action = action
        if dependency_object:
            dependency_object.animation_data.action = action
        if context.bpy_arm_obj.xray.use_custom_motion_names:
            motion_name = context.motion_export_names[motion_name]
        packed_writer.puts(motion_name)
        length = int(action.frame_range[1] - action.frame_range[0] + 1)
        packed_writer.putf('<I', length)
        bone_matrices = {}
        xmatrices = {}
        min_trns = {}
        max_trns = {}
        for frame_index in range(int(action.frame_range[0]), int(action.frame_range[1]) + 1):
            scn.frame_set(frame_index)
            for pose_bone in pose_bones:
                if not bone_matrices.get(pose_bone.name):
                    bone_matrices[pose_bone.name] = []
                    xmatrices[pose_bone.name] = []
                    min_trns[pose_bone.name] = mathutils.Vector((10000.0, 10000.0, 10000.0))
                    max_trns[pose_bone.name] = mathutils.Vector((-10000.0, -10000.0, -10000.0))
                parent = pose_bone.parent
                parent_matrix = parent.matrix.inverted() if parent else imp.MATRIX_BONE_INVERTED
                matrix = context.multiply(parent_matrix, pose_bone.matrix)
                translate = matrix.to_translation()
                for index in range(3):
                    min_trns[pose_bone.name][index] = min(min_trns[pose_bone.name][index], translate[index])
                    max_trns[pose_bone.name][index] = max(max_trns[pose_bone.name][index], translate[index])
                bone_matrices[pose_bone.name].append(matrix)
        if context.high_quality:
            size_max = 0xffff
            trn_max = 0x7fff
            trn_mix = -0x8000
            eps = 0.0000001
        else:
            size_max = 255
            trn_max = 127
            trn_mix = -128
            eps = 0.000001
        for pose_bone in pose_bones:
            flags = 0x0
            if context.high_quality:
                flags |= fmt.KPF_T_HQ
            quaternions = []
            translations = []
            min_tr = min_trns[pose_bone.name]
            max_tr = max_trns[pose_bone.name]
            tr_init = min_tr + (max_tr - min_tr) / 2
            tr_init[2] = -tr_init[2]
            tr_size = (max_tr - min_tr) / size_max
            for matrix in bone_matrices[pose_bone.name]:
                # rotation
                quaternion = matrix.to_quaternion()
                y = int(round(quaternion[1] * 0x7fff, 0))
                z = int(round(quaternion[2] * 0x7fff, 0))
                q = int(round(-quaternion[3] * 0x7fff, 0))
                x = int(round(quaternion[0] * 0x7fff, 0))
                quaternions.append((y, z, q, x))
                # translation
                translate = matrix.to_translation()
                translate[2] = -translate[2]
                if tr_size.length > eps:
                    translate_final = [None, None, None]
                    for index in range(3):
                        if tr_size[index] > 1e-9:
                            value = int((translate[index] - tr_init[index]) / tr_size[index])
                            if value > trn_max:
                                value = trn_max
                            elif value < trn_mix:
                                value = trn_mix
                            translate_final[index] = value
                        else:
                            translate_final[index] = 0
                    translations.append(tuple(translate_final))
                translate_float = tuple(translate)
            if tr_size.length > eps:
                flags |= fmt.FL_T_KEY_PRESENT
            if len(set(quaternions)) != 1:
                packed_writer.putf('<B', flags)
                crc32_temp = 0x0    # temp value
                crc32_offset = len(packed_writer.data)
                packed_writer.putf('<I', crc32_temp)
                for y, z, q, x in quaternions:
                    packed_writer.putf('<4h', y, z, q, x)
                # crc32
                crc32_data_start = crc32_offset + 4
                crc32_data_end = len(packed_writer.data)
                crc32_value = zlib.crc32(
                    packed_writer.data[crc32_data_start : crc32_data_end]
                )
                crc32_packed = struct.pack('<I', crc32_value)
                packed_writer.replace(crc32_offset, crc32_packed)
            else:
                flags |= fmt.FL_R_KEY_ABSENT
                packed_writer.putf('<B', flags)
                packed_writer.putf('<4h', *quaternions[0])
            if flags & fmt.FL_T_KEY_PRESENT:
                crc32_temp = 0x0    # temp value
                crc32_offset = len(packed_writer.data)
                packed_writer.putf('<I', crc32_temp)
                if flags & fmt.KPF_T_HQ:
                    trn_fmt = 'h'
                else:
                    trn_fmt = 'b'
                for translate in translations:
                    packed_writer.putf('<3' + trn_fmt, *translate)
                # crc32
                crc32_data_start = crc32_offset + 4
                crc32_data_end = len(packed_writer.data)
                crc32_value = zlib.crc32(
                    packed_writer.data[crc32_data_start : crc32_data_end]
                )
                crc32_packed = struct.pack('<I', crc32_value)
                packed_writer.replace(crc32_offset, crc32_packed)
                # size, init
                packed_writer.putf('<3f', *tr_size)
                packed_writer.putf('<3f', *tr_init)
            else:
                packed_writer.putf('<3f', *translate_float)
        chunked_writer.put(chunk_id, packed_writer)
        chunk_id += 1
    main_chunked_writer = xray_io.ChunkedWriter()
    main_chunked_writer.put(fmt.Chunks.S_MOTIONS, chunked_writer)
    available_boneparts = []
    available_params = {}
    if context.high_quality:
        partition_version = 4
    else:
        partition_version = 3
    if context.export_mode in ('REPLACE', 'ADD'):
        available_boneparts, available_params = get_motion_params(chunks[fmt.Chunks.S_SMPARAMS])
        if context.export_mode == 'REPLACE' and context.export_bone_parts:
            partition_version = available_boneparts.version
            available_boneparts = []
    packed_writer = xray_io.PackedWriter()
    if not available_boneparts:
        packed_writer.putf('<H', partition_version)
        partitions_count = len(bone_groups)
        packed_writer.putf('<H', partitions_count)
        for bone_group in context.bpy_arm_obj.pose.bone_groups:
            partition_name = bone_group.name
            bones = bone_groups.get(partition_name, None)
            if not bones:
                continue
            packed_writer.puts(partition_name)
            bones_count = len(bones)
            packed_writer.putf('<H', bones_count)
            for bone_name, bone_index in bones:
                packed_writer.puts(bone_name)
                packed_writer.putf('<I', bone_index)
    else:
        packed_writer.putf('<H', available_boneparts.version)
        packed_writer.putf('<H', available_boneparts.count)
        for bonepart in available_boneparts.items:
            packed_writer.puts(bonepart.name)
            packed_writer.putf('<H', bonepart.bones_count)
            for bone in bonepart.bones:
                packed_writer.puts(bone.name)
                packed_writer.putf('<I', bone.index)
    if not available_params:
        packed_writer.putf('<H', motion_count)
        write_motions(context, packed_writer, motions, partition_version)
        main_chunked_writer.put(fmt.Chunks.S_SMPARAMS, packed_writer)
    else:
        if context.export_mode == 'ADD':
            packed_writer.putf('<H', len(available_params) + new_motions_count)
            for motion_name, motion_params in available_params.items():
                packed_writer.puts(motion_name)
                packed_writer.putp(motion_params.writer)
            motions_new = []
            for motion_name, motion_id, has_available in motions:
                if not has_available:
                    motions_new.append((motion_name, motion_id, has_available))
            write_motions(context, packed_writer, motions_new, partition_version)
        elif context.export_mode == 'REPLACE':
            if context.export_motions:
                packed_writer.putf('<H', len(available_params) + new_motions_count)
                for motion_name, motion_params in available_params.items():
                    motion_index = motions_ids.get(motion_name, None)
                    has_available = False
                    if not motion_index is None:
                        _, _, has_available = motions[motion_index]
                    if has_available:
                        packed_writer.puts(motion_name)
                        packed_writer.putp(motion_params.writer)
                    else:
                        params = motion
                        if context.bpy_arm_obj.xray.use_custom_motion_names:
                            motion_name = context.motion_export_names[motion_name]
                        write_motion(context, packed_writer, motion_name, params, partition_version)
                motions_new = []
                for motion_name, motion_id, has_available in motions:
                    if not has_available:
                        motions_new.append((motion_name, motion_id, has_available))
                write_motions(context, packed_writer, motions_new, partition_version)
            else:
                packed_writer.putf('<H', len(available_params))
                for motion_name, motion_params in available_params.items():
                    packed_writer.puts(motion_name)
                    packed_writer.putp(motion_params.writer)
        main_chunked_writer.put(fmt.Chunks.S_SMPARAMS, packed_writer)
    utils.set_mode(mode)
    bpy.context.scene.frame_set(current_frame)
    if current_action:
        context.bpy_arm_obj.animation_data.action = current_action
    else:
        context.bpy_arm_obj.animation_data_clear()
        # reset transforms
        for bone in context.bpy_arm_obj.pose.bones:
            bone.location = (0, 0, 0)
            bone.rotation_euler = (0, 0, 0)
            bone.rotation_quaternion = (1, 0, 0, 0)
            bone.scale = (1, 1, 1)
    if dependency_object:
        if dep_action:
            dependency_object.animation_data.action = dep_action
        else:
            dependency_object.animation_data_clear()
            # reset transforms
            for bone in dependency_object.pose.bones:
                bone.location = (0, 0, 0)
                bone.rotation_euler = (0, 0, 0)
                bone.rotation_quaternion = (1, 0, 0, 0)
                bone.scale = (1, 1, 1)
    return main_chunked_writer


def export_omf_file(context):
    chunked_writer = export_omf(context)
    utils.save_file(context.filepath, chunked_writer)
