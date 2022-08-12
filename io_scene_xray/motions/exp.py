# blender modules
import bpy

# addon modules
from . import const
from . import interp
from . import utilites
from .. import utils
from .. import log
from .. import xray_io


def _export_motion_data(pkw, action, bones_animations, armature, root_bone_names):
    xray = action.xray

    if armature.xray.use_custom_motion_names:
        motion = armature.xray.motions_collection.get(action.name)
        if motion.export_name:
            motion_name = motion.export_name
        else:
            motion_name = action.name
    else:
        motion_name = action.name

    pkw.puts(motion_name)
    frame_start, frame_end = action.frame_range
    pkw.putf('II', int(frame_start), int(frame_end))
    pkw.putf('f', xray.fps)
    pkw.putf('H', 6)  # version
    pkw.putf('<BH', xray.flags, xray.bonepart)
    pkw.putf('<ffff', xray.speed, xray.accrue, xray.falloff, xray.power)
    pkw.putf('H', len(bones_animations))
    for name, animation in bones_animations:
        pkw.puts(name)
        pkw.putf('B', 0)  # flags
        curves = ([], [], [], [], [], [])

        for mat in animation:
            trn = mat.to_translation()
            rot = mat.to_euler('ZXY')
            curves[0].append(+trn[0])
            curves[1].append(+trn[1])
            curves[2].append(-trn[2])
            curves[3].append(-rot[1])
            curves[4].append(-rot[0])
            curves[5].append(+rot[2])

        def curve2keys(curve):
            for frm, val in enumerate(curve):
                yield utilites.KF(frm / xray.fps, val, interp.Shape.STEPPED)

        if name in root_bone_names:
            frame_start, frame_end = action.frame_range
            time_end = (frame_end - frame_start) / xray.fps
        else:
            time_end = None

        for curve_index, curve in enumerate(curves):
            epsilon = utilites.EPSILON
            if xray.autobake_custom_refine:
                if curve_index < 3:
                    epsilon = xray.autobake_refine_location
                else:
                    xray.autobake_refine_rotation

            pkw.putf(
                'BB',
                interp.Behavior.CONSTANT.value,
                interp.Behavior.CONSTANT.value
            )
            cpkw = xray_io.PackedWriter()
            ccnt = utilites.export_keyframes(
                cpkw,
                utilites.refine_keys(curve2keys(curve), epsilon),
                time_end=time_end,
                fps=xray.fps
            )
            pkw.putf('H', ccnt)
            pkw.putp(cpkw)


def _bake_motion_data(action, armature, prepared_bones):
    exportable_bones = [(bone, parent, []) for bone, parent in prepared_bones]

    has_old_action = False
    if armature.animation_data:
        old_act = armature.animation_data.action
        has_old_action = True
    else:
        armature.animation_data_create()
    old_frame = bpy.context.scene.frame_current
    root_bone_names = []
    try:
        armature.animation_data.action = action
        frame_start, frame_end = action.frame_range
        for frame_index in range(int(frame_start), int(frame_end) + 1):
            bpy.context.scene.frame_set(frame_index)
            for pbone, parent, data in exportable_bones:
                if parent:
                    parent_matrix = parent.matrix.inverted()
                else:
                    parent_matrix = const.MATRIX_BONE_INVERTED
                    root_bone_names.append(pbone.name)
                data.append(utils.version.multiply(parent_matrix, pbone.matrix))
    finally:
        if has_old_action:
            armature.animation_data.action = old_act
        bpy.context.scene.frame_set(old_frame)

    return [
        (pbone.name, animation)
        for pbone, _, animation in exportable_bones
    ], root_bone_names


def _prepare_bones(armature):
    def prepare_bone(bone):
        real_parent = utils.find_bone_exportable_parent(bone)
        return (
            armature.pose.bones[bone.name],
            armature.pose.bones[real_parent.name] if real_parent else None
        )

    return [
        prepare_bone(bone)
        for bone in armature.data.bones
            if utils.is_exportable_bone(bone)
    ]


@log.with_context('motion')
def export_motion(pkw, action, armature):
    log.update(action=action.name)
    dependency_object = None
    if armature.xray.dependency_object:
        dependency_object = bpy.data.objects.get(armature.xray.dependency_object)
        if dependency_object:
            old_action = dependency_object.animation_data.action
            dependency_object.animation_data.action = action

    prepared_bones = _prepare_bones(armature)
    bones_animations, root_bone_names = _bake_motion_data(action, armature, prepared_bones)
    _export_motion_data(pkw, action, bones_animations, armature, root_bone_names)

    if dependency_object:
        dependency_object.animation_data.action = old_action


def export_motions(writer, actions, bpy_armature):
    writer.putf('I', len(actions))
    for action in actions:
        export_motion(writer, action, bpy_armature)
