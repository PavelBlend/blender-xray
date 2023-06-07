# blender modules
import bpy

# addon modules
from . import bone
from . import ie
from . import version


def set_arm_initial_state(
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
        bone.reset_pose_bone_transforms(arm_obj)

    # return dependency object state
    if dependency_object:
        if dep_action:
            dependency_object.animation_data.action = dep_action
        else:
            dependency_object.animation_data_clear()
            # reset dependency object transforms
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


def insert_keyframes(frames_coords, fcurves):
    for curve_index in range(len(fcurves)):
        coords = frames_coords[curve_index]
        fcurve = fcurves[curve_index]
        insert_keyframes_for_single_curve(coords, fcurve)


def insert_keyframes_for_single_curve(frames_coords, fcurve, interps=None):
    frames_count = len(frames_coords) // 2

    # create keyframes
    keyframes = fcurve.keyframe_points
    keyframes.add(count=frames_count)
    keyframes.foreach_set('co', frames_coords)

    # set interpolation
    if interps:
        for keyframe, key_interp in zip(keyframes, interps):
            keyframe.interpolation = key_interp

    else:
        # set default linear interpolation
        if version.IS_29:
            interp_prop = bpy.types.Keyframe.bl_rna.properties['interpolation']
            linear = interp_prop.enum_items['LINEAR'].value
            interps = [linear, ] * frames_count
            keyframes.foreach_set('interpolation', interps)
        else:
            for keyframe in keyframes:
                keyframe.interpolation = 'LINEAR'

    fcurve.update()
