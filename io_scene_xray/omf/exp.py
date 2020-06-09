import bpy

from . import fmt, imp
from .. import xray_io


def export_omf_file(filepath, bpy_obj):
    packed_writer = xray_io.PackedWriter()
    scn = bpy.context.scene
    bones = []
    bpy.ops.object.mode_set(mode='POSE')
    for bone in bpy_obj.data.bones:
        if bone.xray.exportable:
            pose_bone = bpy_obj.pose.bones[bone.name]
            bones.append(pose_bone)
    for motion in bpy_obj.xray.motions_collection:
        name = motion.name
        action = bpy.data.actions.get(name)
        if not action:
            continue
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
            for pose_bone in bones:
                if not bone_matrices.get(pose_bone.name):
                    bone_matrices[pose_bone.name] = []
                    bone_parent_matrices[pose_bone.name] = []
                bone_matrices[pose_bone.name].append(pose_bone.matrix)
                if pose_bone.parent:
                    bone_parent_matrices[pose_bone.name].append(pose_bone.parent.matrix.copy())
                else:
                    bone_parent_matrices[pose_bone.name].append(imp.MATRIX_BONE)
        for pose_bone in bones:
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
    bpy.ops.object.mode_set(mode='OBJECT')
