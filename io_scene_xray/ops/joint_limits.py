# standart modules
import math

# blender modules
import bpy

# addon modules
from .. import utils
from .. import text


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


def get_bone_list(obj, mode, report):
    bones = []
    if mode == 'ACTIVE_BONE':
        bone = obj.data.bones.active
        if bone:
            bones.append(bone)
        else:
            report({'ERROR'}, 'No active bone')
    elif mode == 'SELECTED_BONES':
        for bone in obj.data.bones:
            if bone.select:
                bones.append(bone)
        if not bones:
            report({'ERROR'}, 'No selected bones')
    elif mode == 'ALL_BONES':
        for bone in obj.data.bones:
            bones.append(bone)
        if not bones:
            report({'ERROR'}, 'Armature has no bones')
    return bones


class JointLimitsBaseOperator(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return utils.is_armature_context(context)


mode_items = (
    ('ACTIVE_BONE', 'Active Bone', ''),
    ('SELECTED_BONES', 'Selected Bones', ''),
    ('ALL_BONES', 'All Bones', '')
)

op_props = {
    'mode': bpy.props.EnumProperty(
        name='Mode',
        items=mode_items,
        default='SELECTED_BONES'
    ),
}


class XRAY_OT_convert_limits_to_constraints(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.convert_joint_limits'
    bl_label = 'Convert Limits to Constraints'
    bl_description = 'Convert selected bones joint limits to constraints'

    props = op_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.object
        bones = get_bone_list(obj, self.mode, self.report)
        created_count = 0
        for bone in bones:
            xray = bone.xray
            if xray.exportable and xray.ikjoint.type in {'2', '3', '5'}:
                pose_bone = obj.pose.bones[bone.name]
                constraint = pose_bone.constraints.get(CONSTRAINT_NAME, None)
                if not constraint:
                    constraint = pose_bone.constraints.new(
                        type='LIMIT_ROTATION'
                    )
                    constraint.name = CONSTRAINT_NAME
                    created_count += 1
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
        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Constraints created: {}'.format(created_count))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_remove_limits_constraints(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.remove_joint_limits'
    bl_label = 'Remove Limits Constraints'
    bl_description = 'Remove selected bones joint limits constraints'

    props = op_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.object
        bones = get_bone_list(obj, self.mode, self.report)
        removed_count = 0
        for bone in bones:
            pose_bone = obj.pose.bones[bone.name]
            constraint = pose_bone.constraints.get(CONSTRAINT_NAME, None)
            if constraint:
                pose_bone.constraints.remove(constraint)
                removed_count += 1
        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Constraints removed: {}'.format(removed_count))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_convert_ik_to_xray_limits(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.convert_ik_to_xray_limits'
    bl_label = 'Convert IK Limits to XRay Limits'
    bl_description = 'Convert selected bones IK limits to XRay joint limits'

    @utils.set_cursor_state
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
        utils.draw.redraw_areas()
        self.report({'INFO'}, text.get_text(text.warn.ready))
        return {'FINISHED'}


class XRAY_OT_convert_xray_to_ik_limits(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.convert_xray_to_ik_limits'
    bl_label = 'Convert XRay Limits to IK Limits'
    bl_description = 'Convert selected bones XRay joint limits to IK limits'

    @utils.set_cursor_state
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
        utils.draw.redraw_areas()
        self.report({'INFO'}, text.get_text(text.warn.ready))
        return {'FINISHED'}


class XRAY_OT_clear_ik_limits(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.clear_ik_limits'
    bl_label = 'Clear IK Limits'
    bl_description = 'Clear selected bones IK limits'
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        self.layout.label(
            text='IK limits will be removed. Continue?',
            icon='ERROR'
        )

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.object
        for bone in obj.data.bones:
            xray = bone.xray
            if bone.select:
                pose_bone = obj.pose.bones[bone.name]
                pose_bone.use_ik_limit_x = False
                pose_bone.use_ik_limit_y = False
                pose_bone.use_ik_limit_z = False
                pose_bone.ik_min_x = -math.pi
                pose_bone.ik_max_x = math.pi
                pose_bone.ik_min_y = -math.pi
                pose_bone.ik_max_y = math.pi
                pose_bone.ik_min_z = -math.pi
                pose_bone.ik_max_z = math.pi
        utils.draw.redraw_areas()
        self.report({'INFO'}, text.get_text(text.warn.ready))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    XRAY_OT_convert_limits_to_constraints,
    XRAY_OT_remove_limits_constraints,
    XRAY_OT_convert_ik_to_xray_limits,
    XRAY_OT_convert_xray_to_ik_limits,
    XRAY_OT_clear_ik_limits
)


def register():
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
