# blender modules
import bpy


# addon modules
from . import bone
from . import ie


def set_initial_state(
        arm_obj,
        mode,
        current_frame,
        current_action,
        dependency_object,
        dep_action
    ):
    # return initial state
    ie.set_mode(mode)
    bpy.context.scene.frame_set(current_frame)
    if current_action:
        arm_obj.animation_data.action = current_action
    else:
        arm_obj.animation_data_clear()
        # reset transforms
        # TODO: do not delete transformations but keep the original ones
        bone.reset_pose_bone_transforms(arm_obj)

    # return dependency object state
    if dependency_object:
        if dep_action:
            dependency_object.animation_data.action = dep_action
        else:
            dependency_object.animation_data_clear()
            # reset dependency object transforms
            # TODO: do not delete transformations but keep the original ones
            bone.reset_pose_bone_transforms(dependency_object)


def get_initial_state(arm_obj):
    xray = arm_obj.xray
    # remember initial state
    current_frame = bpy.context.scene.frame_current
    mode = arm_obj.mode
    if not arm_obj.animation_data:
        current_action = None
    else:
        current_action = arm_obj.animation_data.action

    # remember dependency object state
    dependency_object = None
    dep_action = None
    if xray.dependency_object:
        dependency_object = bpy.data.objects.get(xray.dependency_object)
        if dependency_object:
            dep_action = dependency_object.animation_data.action

    return current_frame, mode, current_action, dependency_object, dep_action
