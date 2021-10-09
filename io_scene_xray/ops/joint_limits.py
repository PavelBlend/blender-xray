# standart modules
import math

# blender modules
import bpy

# addon modules
from .. import utils


CONSTRAINT_NAME = '!-XRAY-JOINT-LIMITS'


def update_limit(self, context):
    obj = context.object
    if obj.type != 'ARMATURE':
        return
    bone = obj.data.bones.active
    if bone is None:
        return
    ik = bone.xray.ikjoint
    pose_bone = obj.pose.bones[bone.name]
    constraint = pose_bone.constraints.get(CONSTRAINT_NAME, None)
    if not constraint:
        return
    constraint.min_x = ik.lim_x_min
    constraint.max_x = ik.lim_x_max
    constraint.min_y = ik.lim_y_min
    constraint.max_y = ik.lim_y_max
    constraint.min_z = ik.lim_z_min
    constraint.max_z = ik.lim_z_max


class JointLimitsBaseOperator(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return utils.is_armature_context(context)


class XRAY_OT_convert_limits_to_constraints(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.convert_joint_limits'
    bl_label = 'Convert Limits to Constraints'
    bl_description = 'Convert selected bones joint limits to constraints'

    def execute(self, context):
        obj = context.object
        for bone in obj.data.bones:
            xray = bone.xray
            if bone.select and xray.exportable and xray.ikjoint.type in {'2', '3', '5'}:
                pose_bone = obj.pose.bones[bone.name]
                constraint = pose_bone.constraints.get(CONSTRAINT_NAME, None)
                if not constraint:
                    constraint = pose_bone.constraints.new(type='LIMIT_ROTATION')
                    constraint.name = CONSTRAINT_NAME
                constraint.use_limit_x = True
                constraint.use_limit_y = True
                constraint.use_limit_z = True
                constraint.use_transform_limit = True
                constraint.owner_space = 'LOCAL'
                if obj.data.xray.joint_limits_type == 'XRAY':
                    ik = xray.ikjoint
                    constraint.min_x = -ik.lim_x_max
                    constraint.max_x = -ik.lim_x_min
                    constraint.min_y = -ik.lim_y_max
                    constraint.max_y = -ik.lim_y_min
                    constraint.min_z = ik.lim_z_min
                    constraint.max_z = ik.lim_z_max
                else:
                    constraint.min_x = pose_bone.ik_min_x
                    constraint.max_x = pose_bone.ik_max_x
                    constraint.min_y = pose_bone.ik_min_y
                    constraint.max_y = pose_bone.ik_max_y
                    constraint.min_z = pose_bone.ik_min_z
                    constraint.max_z = pose_bone.ik_max_z
        return {'FINISHED'}


class XRAY_OT_remove_limits_constraints(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.remove_joint_limits'
    bl_label = 'Remove Limits Constraints'
    bl_description = 'Remove selected bones joint limits constraints'

    def execute(self, context):
        obj = context.object
        for bone in obj.data.bones:
            if bone.select:
                pose_bone = obj.pose.bones[bone.name]
                constraint = pose_bone.constraints.get(CONSTRAINT_NAME, None)
                if constraint:
                    pose_bone.constraints.remove(constraint)
        return {'FINISHED'}


class XRAY_OT_convert_ik_to_xray_limits(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.convert_ik_to_xray_limits'
    bl_label = 'Convert IK Limits to XRay Limits'
    bl_description = 'Convert selected bones IK limits to XRay joint limits'

    def execute(self, context):
        obj = context.object
        for bone in obj.data.bones:
            xray = bone.xray
            if bone.select:
                pose_bone = obj.pose.bones[bone.name]
                ik = xray.ikjoint
                ik.lim_x_min = -pose_bone.ik_max_x
                ik.lim_x_max = -pose_bone.ik_min_x
                ik.lim_y_min = -pose_bone.ik_max_y
                ik.lim_y_max = -pose_bone.ik_min_y
                ik.lim_z_min = pose_bone.ik_min_z
                ik.lim_z_max = pose_bone.ik_max_z
        return {'FINISHED'}


class XRAY_OT_convert_xray_to_ik_limits(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.convert_xray_to_ik_limits'
    bl_label = 'Convert XRay Limits to IK Limits'
    bl_description = 'Convert selected bones XRay joint limits to IK limits'

    def execute(self, context):
        obj = context.object
        for bone in obj.data.bones:
            xray = bone.xray
            if bone.select:
                pose_bone = obj.pose.bones[bone.name]
                pose_bone.use_ik_limit_x = True
                pose_bone.use_ik_limit_y = True
                pose_bone.use_ik_limit_z = True
                ik = xray.ikjoint
                pose_bone.ik_min_x = -ik.lim_x_max
                pose_bone.ik_max_x = -ik.lim_x_min
                pose_bone.ik_min_y = -ik.lim_y_max
                pose_bone.ik_max_y = -ik.lim_y_min
                pose_bone.ik_min_z = ik.lim_z_min
                pose_bone.ik_max_z = ik.lim_z_max
        return {'FINISHED'}


class XRAY_OT_clear_ik_limits(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.clear_ik_limits'
    bl_label = 'Clear IK Limits'
    bl_description = 'Clear selected bones IK limits'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        for bone in obj.data.bones:
            xray = bone.xray
            if bone.select:
                pose_bone = obj.pose.bones[bone.name]
                ik = xray.ikjoint
                pose_bone.use_ik_limit_x = False
                pose_bone.use_ik_limit_y = False
                pose_bone.use_ik_limit_z = False
                pose_bone.ik_min_x = -math.pi
                pose_bone.ik_max_x = math.pi
                pose_bone.ik_min_y = -math.pi
                pose_bone.ik_max_y = math.pi
                pose_bone.ik_min_z = -math.pi
                pose_bone.ik_max_z = math.pi
        return {'FINISHED'}


classes = (
    XRAY_OT_convert_limits_to_constraints,
    XRAY_OT_remove_limits_constraints,
    XRAY_OT_convert_ik_to_xray_limits,
    XRAY_OT_convert_xray_to_ik_limits,
    XRAY_OT_clear_ik_limits
)


def register():
    for operator in classes:
        bpy.utils.register_class(operator)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
