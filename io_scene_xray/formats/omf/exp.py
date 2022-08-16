# standart modules
import struct
import zlib

# blender modules
import bpy
import mathutils

# addon modules
from . import fmt
from . import imp
from ... import text
from ... import motions
from ... import log
from ... import rw
from ... import utils


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
        self.count = None
        self.items = []


class Motion:
    def __init__(self):
        self.name = None
        self.writer = rw.xray_io.PackedWriter()


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
        raise log.AppError(
            text.error.omf_empty,
            log.props(file=context.filepath)
        )
    chunked_reader = rw.xray_io.ChunkedReader(data)
    chunks = {}
    for chunk_id, chunk_data in chunked_reader:
        chunks[chunk_id] = chunk_data
    chunks_ids = list(chunks.keys())
    if not fmt.Chunks.S_MOTIONS in chunks_ids and context.export_motions:
        raise log.AppError(
            text.error.omf_no_anims,
            log.props(file=context.filepath)
        )
    if not fmt.Chunks.S_SMPARAMS in chunks_ids and context.export_bone_parts:
        raise log.AppError(
            text.error.omf_no_params,
            log.props(file=context.filepath)
        )
    return data, chunks


def get_exclude_motion_names(context):
    data, chunks = validate_omf_file(context)
    motion_names = imp.examine_motions(data)
    return set(motion_names), chunks


def read_bone_parts(packed_reader, params_version):
    bone_parts = BoneParts()
    bone_parts.count = packed_reader.getf('<H')[0]
    bone_indices = []
    bone_names = []
    for partition_index in range(bone_parts.count):
        bonepart = BonePart()
        bonepart.name = packed_reader.gets()
        bonepart.bones_count = packed_reader.getf('<H')[0]
        for bone_index in range(bonepart.bones_count):
            bone = Bone()
            if params_version == 1:
                bone.index = packed_reader.getf('<I')[0]
            elif params_version == 2:
                bone.name = packed_reader.gets()
            elif params_version in (3, 4):
                bone.name = packed_reader.gets()
                bone.index = packed_reader.getf('<I')[0]
            else:
                raise BaseException('Unknown params version')
            bone_indices.append(bone.index)
            bone_names.append(bone.name)
            bonepart.bones.append(bone)
        bone_parts.items.append(bonepart)
    return bone_parts, bone_indices, bone_names


def read_motion_params(packed_reader, params_version):
    motions_params = {}
    motion_count = packed_reader.getf('<H')[0]
    for motion_index in range(motion_count):
        motion = Motion()
        motion.name = packed_reader.gets()
        motion.writer.data.extend(packed_reader.getb(24))
        if params_version == 4:
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
    return motions_params


def get_motion_params(data):
    packed_reader = rw.xray_io.PackedReader(data)
    params_version = packed_reader.getf('<H')[0]
    bone_parts, bone_indices, bone_names = read_bone_parts(packed_reader, params_version)
    motions_params = read_motion_params(packed_reader, params_version)
    return params_version, bone_parts, motions_params, bone_indices, bone_names


def get_motions(context, bones_count):
    # read chunks
    _, chunks = validate_omf_file(context)

    # create chunk reader
    chunked_reader = rw.xray_io.ChunkedReader(chunks[fmt.Chunks.S_MOTIONS])
    chunked_reader.next(fmt.MOTIONS_COUNT_CHUNK)

    motions = {}
    motion_names = []

    for motion_id, chunk_data in chunked_reader:
        # packed writer/reader
        packed_reader = rw.xray_io.PackedReader(chunk_data)
        packed_writer = rw.xray_io.PackedWriter()

        # motion name
        name = packed_reader.gets()
        packed_writer.puts(name)

        # motion length
        length = packed_reader.getf('<I')[0]
        packed_writer.putf('I', length)

        # collect data
        motion_names.append(name)
        motions[name] = (packed_writer, motion_id)

        # bones keyframes
        for bone_index in range(bones_count):
            # flags
            flags = packed_reader.getf('<B')[0]
            t_present = flags & fmt.FL_T_KEY_PRESENT
            r_absent = flags & fmt.FL_R_KEY_ABSENT
            hq = flags & fmt.KPF_T_HQ
            packed_writer.putf('<B', flags)

            # rotation
            if r_absent:
                quaternion = packed_reader.getf('<4h')
                packed_writer.putf('<4h', *quaternion)
            else:
                motion_crc32 = packed_reader.getf('<I')[0]
                packed_writer.putf('<I', motion_crc32)
                for key_index in range(length):
                    quaternion = packed_reader.getf('<4h')
                    packed_writer.putf('<4h', *quaternion)

            # translation
            if t_present:
                if hq:
                    translate_format = '<3h'
                else:
                    translate_format = '<3b'
                motion_crc32 = packed_reader.getf('<I')[0]
                packed_writer.putf('<I', motion_crc32)
                for key_index in range(length):
                    translate = packed_reader.getf(translate_format)
                    packed_writer.putf(translate_format, *translate)
                t_size = packed_reader.getf('<3f')
                packed_writer.putf('<3f', *t_size)
                t_init = packed_reader.getf('<3f')
                packed_writer.putf('<3f', *t_init)
            else:
                translate = packed_reader.getf('<3f')
                packed_writer.putf('<3f', *translate)

    return motions, motion_names, chunks


def write_motion_params(context, writer, name, index, params_version, actions_table):
    action_name = actions_table.get(name)
    action = bpy.data.actions.get(action_name)
    xray = action.xray

    # motion name
    writer.puts(name)

    # flags
    motion_flags = get_flags(xray)
    writer.putf('<I', motion_flags)

    # bone or part
    bone_or_part = xray.bonepart
    writer.putf('<H', bone_or_part)

    # motion index
    writer.putf('<H', index)

    # float-point properties
    writer.putf('<4f', xray.speed, xray.power, xray.accrue, xray.falloff)

    # motion marks
    if params_version == 4:
        marks_count = 0
        writer.putf('<I', marks_count)


def write_motions_params(context, writer, motions, version, actions_table):
    for name, index, _ in motions:
        write_motion_params(context, writer, name, index, version, actions_table)


def set_initial_state(
        context,
        mode,
        current_frame,
        current_action,
        dependency_object,
        dep_action
    ):
    # return initial state
    utils.set_mode(mode)
    bpy.context.scene.frame_set(current_frame)
    if current_action:
        context.bpy_arm_obj.animation_data.action = current_action
    else:
        context.bpy_arm_obj.animation_data_clear()
        # reset transforms
        # TODO: do not delete transformations but keep the original ones
        utils.reset_pose_bone_transforms(context.bpy_arm_obj)

    # return dependency object state
    if dependency_object:
        if dep_action:
            dependency_object.animation_data.action = dep_action
        else:
            dependency_object.animation_data_clear()
            # reset dependency object transforms
            # TODO: do not delete transformations but keep the original ones
            utils.reset_pose_bone_transforms(dependency_object)


def get_initial_state(context, xray):
    # remember initial state
    current_frame = bpy.context.scene.frame_current
    mode = context.bpy_arm_obj.mode
    if not context.bpy_arm_obj.animation_data:
        current_action = None
    else:
        current_action = context.bpy_arm_obj.animation_data.action

    # remember dependency object state
    dependency_object = None
    dep_action = None
    if xray.dependency_object:
        dependency_object = bpy.data.objects.get(xray.dependency_object)
        if dependency_object:
            dep_action = dependency_object.animation_data.action

    return current_frame, mode, current_action, dependency_object, dep_action


def get_pose_bones_and_groups(context):
    # collect pose bones and bone groups
    utils.set_mode('POSE')
    pose_bones = []
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
        raise log.AppError(
            text.error.omf_bone_no_group,
            log.props(
                armature_object=context.bpy_arm_obj.name,
                bones=no_group_bones
            )
        )
    return pose_bones, bone_groups


def export_motion_params(
        context,
        xray,
        packed_writer,
        available_params,
        motion_count,
        new_motions_count,
        motions,
        motions_ids,
        params_version,
        motion_export_names,
        actions_table
    ):
    if not available_params:
        # overwrite mode
        packed_writer.putf('<H', motion_count)
        write_motions_params(context, packed_writer, motions, params_version, actions_table)
    else:

        # add mode
        if context.export_mode == 'ADD':
            packed_writer.putf('<H', len(available_params) + new_motions_count)
            for motion_name, motion_params in available_params.items():
                packed_writer.puts(motion_name)
                packed_writer.putp(motion_params.writer)
            motions_new = []
            for motion_name, motion_id, has_available in motions:
                if not has_available:
                    motions_new.append((motion_name, motion_id, has_available))
            write_motions_params(context, packed_writer, motions_new, params_version, actions_table)

        # replace mode
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
                        if xray.use_custom_motion_names:
                            motion_name = motion_export_names[motion_name]
                        write_motion_params(context, packed_writer, motion_name, params, params_version, actions_table)
                motions_new = []
                for motion_name, motion_id, has_available in motions:
                    if not has_available:
                        motions_new.append((motion_name, motion_id, has_available))
                write_motions_params(context, packed_writer, motions_new, params_version, actions_table)
            else:
                packed_writer.putf('<H', len(available_params))
                for motion_name, motion_params in available_params.items():
                    packed_writer.puts(motion_name)
                    packed_writer.putp(motion_params.writer)


def export_boneparts(
        context,
        packed_writer,
        available_boneparts,
        params_version,
        bone_groups
    ):
    if not available_boneparts:
        packed_writer.putf('<H', params_version)
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
        packed_writer.putf('<H', params_version)
        packed_writer.putf('<H', available_boneparts.count)
        for bonepart in available_boneparts.items:
            packed_writer.puts(bonepart.name)
            packed_writer.putf('<H', bonepart.bones_count)
            for bone in bonepart.bones:
                packed_writer.puts(bone.name)
                packed_writer.putf('<I', bone.index)


def collect_bones(context, bone_names, bone_indices, bones_count):
    # collect bones by names and indices
    export_bones = []
    if bone_names and bone_indices:
        export_bones = [None] * len(bone_names)
        for bone_name, bone_index in zip(bone_names, bone_indices):
            pose_bone = context.bpy_arm_obj.pose.bones.get(bone_name, None)
            if pose_bone:
                export_bones[bone_index] = pose_bone
            else:
                # TODO: error, cannot find bone
                export_bones = []
                break

    # collect bones by names
    if not export_bones:
        if bone_names:
            for bone_name in bone_names:
                pose_bone = context.bpy_arm_obj.pose.bones.get(bone_name, None)
                if pose_bone:
                    export_bones.append(pose_bone)
                else:
                    export_bones = []
                    break

    # collect bones by indices
    if not export_bones:
        if bone_indices:
            if len(bone_indices) == bones_count:
                for bone_index in bone_indices:
                    if bone_index >= bones_count:
                        export_bones = []
                        break
                    pose_bone = context.bpy_arm_obj.pose.bones[bone_index]
                    if pose_bone:
                        export_bones.append(pose_bone)
                    else:
                        export_bones = []
                        break

    # collect bones by pose bones
    if not export_bones:
        for bone in context.bpy_arm_obj.data.bones:
            if utils.is_exportable_bone(bone):
                pose_bone = context.bpy_arm_obj.pose.bones[bone.name]
                export_bones.append(pose_bone)

    return export_bones


def collect_motion_names(context, xray):
    motion_export_names = {}
    actions_table = {}
    for motion in xray.motions_collection:
        if xray.use_custom_motion_names:
            if motion.export_name:
                export_name = motion.export_name
            else:
                export_name = motion.name
        else:
            export_name = motion.name
        motion_export_names[motion.name] = export_name
        actions_table[export_name] = motion.name
    return motion_export_names, actions_table


def calculate_bones_count(context):
    bones_count = 0
    for bone in context.bpy_arm_obj.data.bones:
        if utils.is_exportable_bone(bone):
            bones_count += 1
    return bones_count


def search_available_data(context, bones_count, motion_export_names):
    chunks = None
    if context.export_mode in ('ADD', 'REPLACE'):
        available_motions, available_motion_names, chunks = get_motions(context, bones_count)
        export_motion_names = []
        export_motion_names.extend(available_motion_names)
        export_motion_names.extend(
            list(set(motion_export_names.values()) - set(available_motion_names))
        )
    else:
        available_motions = {}
        export_motion_names = list(motion_export_names.values())
    return available_motions, export_motion_names, chunks


def collect_motions_availability_table(context, export_motion_names, available_motions, actions_table):
    motion_count = 0
    motions = []
    motions_ids = {}
    if context.export_mode == 'OVERWRITE':
        available = False
        for motion_name in export_motion_names:
            action_name = actions_table.get(motion_name, None)
            if action_name:
                action = bpy.data.actions.get(action_name)
            else:
                action = None
            if not action:
                # TODO: added warning
                continue
            motions.append((motion_name, motion_count, available))
            motions_ids[motion_name] = motion_count
            motion_count += 1
    else:
        for motion_name in export_motion_names:
            action_name = actions_table.get(motion_name, None)
            if action_name:
                action = bpy.data.actions.get(action_name)
            else:
                action = None
            _, motion_id = available_motions.get(motion_name, (None, None))
            if not action:
                if motion_id is None:
                    # TODO: added warning
                    continue
            if not motion_id is None:
                available = True
                motions.append((motion_name, motion_id, available))
            else:
                available = False
                motions.append((motion_name, motion_count, available))
            motions_ids[motion_name] = motion_count
            motion_count += 1
    return motion_count, motions, motions_ids


def get_available_params_and_boneparts(context, chunks):
    available_boneparts = []
    available_params = {}

    if context.high_quality:
        params_version = 4
    else:
        params_version = 3

    bone_indices = None
    bone_names = None
    if context.export_mode in ('REPLACE', 'ADD'):
        (
            available_version,
            available_boneparts,
            available_params,
            bone_indices,
            bone_names
        ) = get_motion_params(chunks[fmt.Chunks.S_SMPARAMS])
        if context.export_mode == 'REPLACE' and context.export_bone_parts:
            available_boneparts = []
        params_version = available_version
    return params_version, available_params, available_boneparts, bone_names, bone_indices


def export_motions(
        context,
        motions_writer,
        export_motion_names,
        available_motions,
        dependency_object,
        pose_bones,
        export_bones,
        actions_table,
        motion_export_names
    ):
    scn = bpy.context.scene
    new_motions_count = 0
    chunk_id = fmt.MOTIONS_COUNT_CHUNK + 1
    object_motions = motion_export_names.values()
    for motion_name in export_motion_names:
        action_name = actions_table.get(motion_name, None)
        if action_name:
            action = bpy.data.actions.get(action_name)
        else:
            action = None

        packed_writer, _ = available_motions.get(motion_name, (None, None))

        if context.export_mode == 'ADD':
            if packed_writer:
                motions_writer.put(chunk_id, packed_writer)
                chunk_id += 1
                continue

        elif context.export_mode == 'REPLACE':
            if packed_writer:
                if not motion_name in object_motions:
                    motions_writer.put(chunk_id, packed_writer)
                    chunk_id += 1
                    continue

        if not action:
            if context.export_mode == 'REPLACE':
                if packed_writer is None:
                    continue
                else:
                    motions_writer.put(chunk_id, packed_writer)
                    chunk_id += 1
                    continue
            else:
                continue

        if context.export_mode == 'ADD':
            new_motions_count += 1
        elif context.export_mode == 'REPLACE':
            if packed_writer is None:
                new_motions_count += 1

        packed_writer = rw.xray_io.PackedWriter()
        context.bpy_arm_obj.animation_data.action = action

        if dependency_object:
            dependency_object.animation_data.action = action

        # name
        packed_writer.puts(motion_name)

        # length
        length = int(action.frame_range[1] - action.frame_range[0] + 1)
        packed_writer.putf('<I', length)

        bone_matrices = {}
        unique_translate = {}
        start_frame = int(action.frame_range[0])
        end_frame = int(action.frame_range[1])

        # collect pose bone matrices
        for frame_index in range(start_frame, end_frame + 1):
            scn.frame_set(frame_index)

            for pose_bone in pose_bones:
                name = pose_bone.name
                parent = pose_bone.parent
                if parent:
                    parent_matrix = parent.matrix.inverted()
                else:
                    parent_matrix = motions.const.MATRIX_BONE_INVERTED
                matrix = context.multiply(parent_matrix, pose_bone.matrix)
                trn = matrix.to_translation()
                trn[2] = -trn[2]
                unique_translate.setdefault(name, set()).add(tuple(trn))
                bone_matrices.setdefault(name, []).append(matrix)

        # calculate f-curve amplitude
        min_translate = {}
        max_translate = {}
        for bone_name, translate in unique_translate.items():
            # min
            min_x = min(translate, key=lambda i: i[0])[0]
            min_y = min(translate, key=lambda i: i[1])[1]
            min_z = min(translate, key=lambda i: i[2])[2]
            min_translate[bone_name] = mathutils.Vector((min_x, min_y, min_z))
            # max
            max_x = max(translate, key=lambda i: i[0])[0]
            max_y = max(translate, key=lambda i: i[1])[1]
            max_z = max(translate, key=lambda i: i[2])[2]
            max_translate[bone_name] = mathutils.Vector((max_x, max_y, max_z))

        # set limits
        if context.high_quality:
            size_max = 0xffff
            trn_max = 0x7fff
            trn_mix = -0x8000
        else:
            size_max = 255
            trn_max = 127
            trn_mix = -128

        # export keyframes
        for pose_bone in export_bones:
            quaternions = []
            translations = []

            min_tr = min_translate[pose_bone.name]
            max_tr = max_translate[pose_bone.name]

            tr_init = min_tr + (max_tr - min_tr) / 2
            tr_size = (max_tr - min_tr) / size_max

            # flags
            flags = 0x0
            if context.high_quality:
                flags |= fmt.KPF_T_HQ

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
                translate_final = [None, None, None]
                for index in range(3):
                    if tr_size[index] > 0.000000001:
                        value = int((translate[index] - tr_init[index]) / tr_size[index])
                    else:
                        value = 0
                    if value > trn_max:
                        value = trn_max
                    elif value < trn_mix:
                        value = trn_mix
                    translate_final[index] = value
                translations.append(tuple(translate_final))
                translate_float = tuple(translate)

                if len(set(translations)) != 1:
                    flags |= fmt.FL_T_KEY_PRESENT

            # write rotation
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

            # write translation
            if flags & fmt.FL_T_KEY_PRESENT:
                crc32_temp = 0x0    # temp value
                crc32_offset = len(packed_writer.data)
                packed_writer.putf('<I', crc32_temp)
                if context.high_quality:
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

        motions_writer.put(chunk_id, packed_writer)
        chunk_id += 1
    return new_motions_count


def export_omf(context):
    xray = context.bpy_arm_obj.xray

    (
        current_frame,
        mode,
        current_action,
        dependency_object,
        dep_action
    ) = get_initial_state(context, xray)

    motion_export_names, actions_table = collect_motion_names(context, xray)
    bones_count = calculate_bones_count(context)

    available_motions, export_motion_names, chunks = search_available_data(
        context,
        bones_count,
        motion_export_names
    )

    pose_bones, bone_groups = get_pose_bones_and_groups(context)

    motion_count, motions, motions_ids = collect_motions_availability_table(
        context,
        export_motion_names,
        available_motions,
        actions_table
    )

    # motions chunked writer
    motions_writer = rw.xray_io.ChunkedWriter()

    # write motions count chunk
    packed_writer = rw.xray_io.PackedWriter()
    packed_writer.putf('<I', motion_count)
    motions_writer.put(fmt.MOTIONS_COUNT_CHUNK, packed_writer)

    context.bpy_arm_obj.animation_data_create()

    (
        params_version,
        available_params,
        available_boneparts,
        bone_names,
        bone_indices
    ) = get_available_params_and_boneparts(context, chunks)

    export_bones = collect_bones(
        context,
        bone_names,
        bone_indices,
        bones_count
    )

    new_motions_count = export_motions(
        context,
        motions_writer,
        export_motion_names,
        available_motions,
        dependency_object,
        pose_bones,
        export_bones,
        actions_table,
        motion_export_names
    )

    main_chunked_writer = rw.xray_io.ChunkedWriter()
    # write motions chunk
    main_chunked_writer.put(fmt.Chunks.S_MOTIONS, motions_writer)

    packed_writer = rw.xray_io.PackedWriter()

    export_boneparts(
        context,
        packed_writer,
        available_boneparts,
        params_version,
        bone_groups
    )

    export_motion_params(
        context,
        xray,
        packed_writer,
        available_params,
        motion_count,
        new_motions_count,
        motions,
        motions_ids,
        params_version,
        motion_export_names,
        actions_table
    )

    # write params chunk
    main_chunked_writer.put(fmt.Chunks.S_SMPARAMS, packed_writer)

    set_initial_state(
        context,
        mode,
        current_frame,
        current_action,
        dependency_object,
        dep_action
    )

    return main_chunked_writer


@log.with_context('export-omf')
def export_omf_file(context):
    log.update(object=context.bpy_arm_obj.name)
    chunked_writer = export_omf(context)
    utils.save_file(context.filepath, chunked_writer)
