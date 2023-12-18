# blender modules
import bpy
import mathutils

# addon modules
from . import const
from . import write
from . import interp
from . import utilites
from ... import utils
from ... import log
from ... import rw


MOTION_DEFAULT_FLAGS = 0


def convert_curve_to_keys(curve, fps):
    for frame, value in enumerate(curve):
        yield interp.KeyFrame(frame / fps, value, interp.Shape.STEPPED)


def _export_motion_data(
        writer,
        action,
        bones_anims,
        armature,
        root_bone_names,
        root_obj
    ):

    xray = action.xray

    # search motion name
    motion_name = action.name
    if armature.xray.use_custom_motion_names:
        motion = armature.xray.motions_collection.get(action.name)
        if motion.export_name:
            motion_name = motion.export_name

    # collect motion parameters
    frame_start, frame_end = action.frame_range
    fps = xray.fps
    bones_count = len(bones_anims)

    # write motion parameters
    writer.puts(motion_name)
    writer.putf('<2I', int(frame_start), int(frame_end))
    writer.putf('<f', fps)
    writer.putf('<H', const.FORMAT_VERSION_6)
    writer.putf('<B', xray.flags)
    writer.putf('<H', xray.bonepart)
    writer.putf('<4f', xray.speed, xray.accrue, xray.falloff, xray.power)
    writer.putf('<H', bones_count)

    # search epsilon value
    if xray.autobake_custom_refine:
        epsilon_loc = xray.autobake_refine_location
        epsilon_rot = xray.autobake_refine_rotation
    else:
        epsilon_loc = const.EPSILON
        epsilon_rot = const.EPSILON

    epsilons = [epsilon_loc, epsilon_rot]
    _, scale = utils.ie.get_obj_scale_matrix(root_obj, armature)
    if scale == mathutils.Vector((1.0, 1.0, 1.0)):
        scale = None

    # write motions
    for bone, bone_anim in bones_anims:
        # write bone motion parameters
        writer.puts(bone.name)
        writer.putf('<B', MOTION_DEFAULT_FLAGS)

        # collect translation and rotation curves
        curves = []
        for curve_id in range(const.CURVE_COUNT):
            curves.append([])

        if scale:
            for matrix in bone_anim:
                translate = matrix.to_translation()
                translate.x *= scale.x
                translate.y *= scale.y
                translate.z *= scale.z
                rotate = matrix.to_euler('ZXY')

                curves[0].append(+translate[0])
                curves[1].append(+translate[1])
                curves[2].append(-translate[2])
                curves[3].append(-rotate[1])
                curves[4].append(-rotate[0])
                curves[5].append(+rotate[2])

        else:
            for matrix in bone_anim:
                translate = matrix.to_translation()
                rotate = matrix.to_euler('ZXY')

                curves[0].append(+translate[0])
                curves[1].append(+translate[1])
                curves[2].append(-translate[2])
                curves[3].append(-rotate[1])
                curves[4].append(-rotate[0])
                curves[5].append(+rotate[2])

        if bone.name in root_bone_names:
            time_end = (frame_end - frame_start) / fps
        else:
            time_end = None

        for curve_index, curve in enumerate(curves):
            epsilon = epsilons[curve_index // 3]

            # write behavior
            writer.putf(
                '<2B',
                interp.Behavior.CONSTANT.value,
                interp.Behavior.CONSTANT.value
            )

            # write keyframes
            keyframes_writer = rw.write.PackedWriter()
            keyframes = utilites.refine_keys(
                convert_curve_to_keys(curve, fps),
                epsilon
            )
            keyframes_count = write.export_keyframes(
                keyframes_writer,
                keyframes,
                time_end=time_end,
                fps=fps
            )
            writer.putf('<H', keyframes_count)
            writer.putp(keyframes_writer)


def _bake_motion_data(action, armature):
    exportable_bones = _prepare_bones(armature)

    # find preview action
    anim_data = armature.animation_data
    if anim_data:
        act_old = anim_data.action
    else:
        act_old = None
        anim_data = armature.animation_data_create()

    frame_old = bpy.context.scene.frame_current

    try:
        root_bone_names = set()
        anim_data.action = action
        frame_start = int(action.frame_range[0])
        frame_end = int(action.frame_range[1])
        multiply = utils.version.get_multiply()

        for frame_index in range(frame_start, frame_end + 1):
            bpy.context.scene.frame_set(frame_index)
            for bone, parent, data in exportable_bones:
                if parent:
                    parent_matrix = parent.matrix.inverted()
                else:
                    parent_matrix = const.MATRIX_BONE_INVERTED
                    root_bone_names.add(bone.name)
                matrix = multiply(parent_matrix, bone.matrix)
                data.append(matrix)

    finally:
        if act_old:
            anim_data.action = act_old
        bpy.context.scene.frame_set(frame_old)

    for bone_anim in exportable_bones:
        # remove bone parent
        bone_anim.pop(1)

    return exportable_bones, root_bone_names


def _prepare_bone(armature, bone):
    pose_bone = armature.pose.bones[bone.name]
    real_parent = utils.bone.find_bone_exportable_parent(bone)
    if real_parent:
        pose_bone_parent = armature.pose.bones[real_parent.name]
    else:
        pose_bone_parent = None
    anim_data = []
    return [pose_bone, pose_bone_parent, anim_data]


def _prepare_bones(armature):
    return [
        _prepare_bone(armature, bone)
        for bone in armature.data.bones
            if utils.bone.is_exportable_bone(bone)
    ]


@log.with_context('motion')
def export_motion(writer, action, armature, root_obj):
    log.update(action=action.name)

    dep_obj = None
    dep_obj_name = armature.xray.dependency_object
    if dep_obj_name:
        dep_obj = bpy.data.objects.get(dep_obj_name)
        if dep_obj:
            old_action = dep_obj.animation_data.action
            dep_obj.animation_data.action = action

    # bake
    bones_anims, root_bone_names = _bake_motion_data(
        action,
        armature
    )

    # export
    _export_motion_data(
        writer,
        action,
        bones_anims,
        armature,
        root_bone_names,
        root_obj
    )

    if dep_obj:
        dep_obj.animation_data.action = old_action


def export_motions(writer, actions, bpy_armature, root_obj):
    (
        current_frame,
        mode,
        current_action,
        dependency_object,
        dep_action
    ) = utils.action.get_initial_state(bpy_armature)

    motions_count = len(actions)
    writer.putf('<I', motions_count)
    for action in actions:
        export_motion(writer, action, bpy_armature, root_obj)

    utils.action.set_arm_initial_state(
        bpy_armature,
        mode,
        current_frame,
        current_action,
        dependency_object,
        dep_action
    )
