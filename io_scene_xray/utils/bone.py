def is_exportable_bone(bpy_bone):
    return bpy_bone.xray.exportable


def find_bone_exportable_parent(bpy_bone):
    result = bpy_bone.parent
    while (result is not None) and not is_exportable_bone(result):
        result = result.parent
    return result


def reset_pose_bone_transforms(armature_object):
    for bone in armature_object.pose.bones:
        bone.location = (0, 0, 0)
        bone.rotation_euler = (0, 0, 0)
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.scale = (1, 1, 1)
