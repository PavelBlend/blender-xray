import bpy

from . import fmt, imp
from .. import xray_io, utils


def export_omf_file(filepath, bpy_obj):
    scn = bpy.context.scene
    pose_bones = []
    bpy.ops.object.mode_set(mode='POSE')
    bone_groups = {}
    for bone_index, bone in enumerate(bpy_obj.data.bones):
        if bone.xray.exportable:
            pose_bone = bpy_obj.pose.bones[bone.name]
            if not pose_bone.bone_group:
                raise utils.AppError(
                    'Bone "{}" of "{}" armature does not have a bone group'.format(
                        pose_bone.name, bpy_obj.name)
                    )
            if not bone_groups.get(pose_bone.bone_group.name, None):
                bone_groups[pose_bone.bone_group.name] = []
            bone_groups[pose_bone.bone_group.name].append((pose_bone.name, bone_index))
            pose_bones.append(pose_bone)
    motion_count = 0
    motions = {}
    for motion in bpy_obj.xray.motions_collection:
        name = motion.name
        action = bpy.data.actions.get(name)
        if not action:
            continue
        motions[name] = [motion_count, ]
        motion_count += 1
    chunked_writer = xray_io.ChunkedWriter()
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('I', motion_count)
    chunked_writer.put(fmt.MOTIONS_COUNT_CHUNK, packed_writer)
    chunk_id = fmt.MOTIONS_COUNT_CHUNK + 1
    for motion in bpy_obj.xray.motions_collection:
        name = motion.name
        action = bpy.data.actions.get(name)
        if not action:
            continue
        packed_writer = xray_io.PackedWriter()
        bpy_obj.animation_data_create()
        bpy_obj.animation_data.action = action
        packed_writer.puts(name)
        length = int(action.frame_range[1] - action.frame_range[0])
        packed_writer.putf('I', length)
        flags = fmt.FL_T_KEY_PRESENT
        packed_writer.putf('B', flags)
        bone_matrices = {}
        bone_parent_matrices = {}
        for frame_index in range(int(action.frame_range[0]), int(action.frame_range[1]) + 1):
            scn.frame_set(frame_index)
            for pose_bone in pose_bones:
                if not bone_matrices.get(pose_bone.name):
                    bone_matrices[pose_bone.name] = []
                    bone_parent_matrices[pose_bone.name] = []
                bone_matrices[pose_bone.name].append(pose_bone.matrix)
                if pose_bone.parent:
                    bone_parent_matrices[pose_bone.name].append(pose_bone.parent.matrix.copy())
                else:
                    bone_parent_matrices[pose_bone.name].append(imp.MATRIX_BONE)
        for pose_bone in pose_bones:
            motion_crc32 = 0x0    # temp value
            packed_writer.putf('I', motion_crc32)
            for matrix_index, matrix in enumerate(bone_matrices[pose_bone.name]):
                # quaternion
                packed_writer.putf('4h', 1, 1, 1, 1)    # temp values
            motion_crc32 = 0x0    # temp value
            packed_writer.putf('I', motion_crc32)
            for matrix_index, matrix in enumerate(bone_matrices[pose_bone.name]):
                # translation
                packed_writer.putf('3b', 0, 0, 0)    # temp values
            packed_writer.putf('3f', 1, 1, 1)    # t_size
            packed_writer.putf('3f', 0, 0, 0)    # t_init
            packed_writer.putf('3f', 0, 0, 0)    # t_init
        chunked_writer.put(chunk_id, packed_writer)
        chunk_id += 1
    main_chunked_writer = xray_io.ChunkedWriter()
    main_chunked_writer.put(fmt.Chunks.S_MOTIONS, chunked_writer)
    packed_writer = xray_io.PackedWriter()
    partition_version = 3
    packed_writer.putf('H', partition_version)
    partitions_count = len(bone_groups)
    packed_writer.putf('H', partitions_count)
    for bone_group in bpy_obj.pose.bone_groups:
        partition_name = bone_group.name
        packed_writer.puts(partition_name)
        bones = bone_groups[partition_name]
        if not bones:
            raise utils.AppError('Armature "{}" has an empty bone group'.format(bpy_obj.name))
        bones_count = len(bones)
        packed_writer.putf('H', bones_count)
        for bone_name, bone_index in bones:
            packed_writer.puts(bone_name)
            packed_writer.putf('I', bone_index)
    packed_writer.putf('H', motion_count)
    bone_groups_indices = {}
    for group_index, bone_group in enumerate(bpy_obj.pose.bone_groups):
        bone_groups_indices[bone_group.name] = group_index
    for motion_name, motion_params in motions.items():
        action = bpy.data.actions.get(motion_name)
        packed_writer.puts(motion_name)
        motion_flags = 0    # temp value
        packed_writer.putf('I', motion_flags)
        if not action.xray.bonepart_name:
            raise utils.AppError('The action "{}" does not have a bone part'.format(action.name))
        bone_or_part = bone_groups_indices[action.xray.bonepart_name]
        packed_writer.putf('H', bone_or_part)
        motion = motion_params[0]
        packed_writer.putf('H', motion)
        packed_writer.putf('f', action.xray.speed)
        packed_writer.putf('f', action.xray.power)
        packed_writer.putf('f', action.xray.accrue)
        packed_writer.putf('f', action.xray.falloff)
    main_chunked_writer.put(fmt.Chunks.S_SMPARAMS, packed_writer)
    bpy.ops.object.mode_set(mode='OBJECT')
    with open(filepath, 'wb') as file:
        file.write(main_chunked_writer.data)
