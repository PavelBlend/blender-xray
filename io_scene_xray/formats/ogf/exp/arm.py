# addon modules
from . import bone
from .... import text
from .... import log
from .... import utils


def scan_arm(bpy_obj, arms, bones, bones_map):
    arms.append(bpy_obj)

    for bpy_bone in bpy_obj.data.bones:

        if not utils.bone.is_exportable_bone(bpy_bone):
            continue

        bone.reg_bone(bones, bones_map, bpy_bone, bpy_obj)


def get_arm_scale(root_obj, arm_obj):
    _, scale_vec = utils.ie.get_obj_scale_matrix(root_obj, arm_obj)
    scale = utils.ie.check_armature_scale(scale_vec, root_obj, arm_obj)
    return scale


def get_arm(root_obj, arms):

    if len(arms) > 1:
        raise log.AppError(
            text.error.object_many_arms,
            log.props(
                root_object=root_obj.name,
                armatures=[arm.name for arm in arms]
            )
        )

    elif len(arms) == 1:
        arm_obj = arms[0]

    else:
        arm_obj = None

    return arm_obj
