# standart modules
import math

# blender modules
import bpy
import mathutils

# addon modules
from .. import utils
from .. import text


CONSTRAINT_NAME = '!-XRAY-JOINT-LIMITS'


def update_limit(self, context):
    obj = context.active_object
    if obj and obj.type != 'ARMATURE':
        return

    bone = obj.data.bones.active
    if bone is None:
        return

    ik = bone.xray.ikjoint

    if ik.lim_x_min > 0.0:
        ik.lim_x_min = -ik.lim_x_min
    if ik.lim_x_max < 0.0:
        ik.lim_x_max = -ik.lim_x_max

    if ik.lim_y_min > 0.0:
        ik.lim_y_min = -ik.lim_y_min
    if ik.lim_y_max < 0.0:
        ik.lim_y_max = -ik.lim_y_max

    if ik.lim_z_min > 0.0:
        ik.lim_z_min = -ik.lim_z_min
    if ik.lim_z_max < 0.0:
        ik.lim_z_max = -ik.lim_z_max

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


def update_slider(self, context):
    obj = context.active_object
    if obj and obj.type != 'ARMATURE':
        return

    bone = obj.data.bones.active
    if bone is None:
        return

    ik = bone.xray.ikjoint

    if ik.slide_min > 0.0:
        ik.slide_min = -ik.slide_min

    if ik.slide_max < 0.0:
        ik.slide_max = -ik.slide_max


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


class JointLimitsBaseOperator(utils.ie.BaseOperator):
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return utils.obj.is_armature_context(context)


class XRAY_OT_convert_limits_to_constraints(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.convert_joint_limits'
    bl_label = 'Convert Limits to Constraints'
    bl_description = 'Convert selected bones joint limits to constraints'

    mode = bpy.props.EnumProperty(
        name='Mode',
        items=(
            ('ACTIVE_BONE', 'Active Bone', ''),
            ('SELECTED_BONES', 'Selected Bones', ''),
            ('ALL_BONES', 'All Bones', '')
        ),
        default='SELECTED_BONES'
    )

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.active_object
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

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_remove_limits_constraints(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.remove_joint_limits'
    bl_label = 'Remove Limits Constraints'
    bl_description = 'Remove selected bones joint limits constraints'

    mode = bpy.props.EnumProperty(
        name='Mode',
        items=(
            ('ACTIVE_BONE', 'Active Bone', ''),
            ('SELECTED_BONES', 'Selected Bones', ''),
            ('ALL_BONES', 'All Bones', '')
        ),
        default='SELECTED_BONES'
    )

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.active_object
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

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_convert_ik_to_xray_limits(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.convert_ik_to_xray_limits'
    bl_label = 'Convert IK Limits to X-Ray Limits'
    bl_description = 'Convert selected bones IK limits to X-Ray joint limits'

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.active_object
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
    bl_label = 'Convert X-Ray Limits to IK Limits'
    bl_description = 'Convert selected bones X-Ray joint limits to IK limits'

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.active_object
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

    def draw(self, context):    # pragma: no cover
        self.layout.label(
            text='IK limits will be removed. Continue?',
            icon='ERROR'
        )

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.active_object
        for bone in obj.data.bones:
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

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_set_joint_limits(JointLimitsBaseOperator):
    bl_idname = 'io_scene_xray.set_joint_limits'
    bl_label = 'Set Joint Limits'
    bl_description = 'Set joint limits by pose bone rotation'
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        name='Mode',
        items=(
            ('MIN_X', 'Min X', ''),
            ('MAX_X', 'Max X', ''),

            ('MIN_Y', 'Min Y', ''),
            ('MAX_Y', 'Max Y', ''),

            ('MIN_Z', 'Min Z', ''),
            ('MAX_Z', 'Max Z', ''),

            ('MIN_MAX_X', 'Min/Max X', ''),
            ('MIN_MAX_Y', 'Min/Max Y', ''),
            ('MIN_MAX_Z', 'Min/Max Z', ''),

            ('MIN_XYZ', 'Min XYZ', ''),
            ('MAX_XYZ', 'Max XYZ', '')
        ),
        default='MIN_XYZ'
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and context.active_pose_bone

    @utils.set_cursor_state
    def execute(self, context):
        pose_bone = context.active_pose_bone
        ik = pose_bone.bone.xray.ikjoint

        # get bone rotation
        if pose_bone.rotation_mode == 'QUATERNION':
            rot_mat = pose_bone.rotation_quaternion.to_matrix()

        elif pose_bone.rotation_mode == 'AXIS_ANGLE':
            rot_mat = mathutils.Matrix.Rotation(
                pose_bone.rotation_axis_angle[0],
                4,
                pose_bone.rotation_axis_angle[1:]
            )

        else:
            rot_mat = pose_bone.rotation_euler.to_matrix()

        rot = rot_mat.to_euler('ZXY')
        rot.x *= -1.0
        rot.y *= -1.0

        # clipping value
        if self.mode.startswith('MIN_MAX'):
            for axis in range(3):
                rot[axis] = abs(rot[axis])

        else:
            for axis in range(3):
                value = rot[axis]
                clip = False

                if self.mode.startswith('MIN'):
                    if value > 0.0:
                        clip = True

                else:
                    if value < 0.0:
                        clip = True

                if clip:
                    rot[axis] = 0.0

        # set min limits
        if self.mode in ('MIN_X'):
            ik.lim_x_min = rot.x

        elif self.mode in ('MIN_Y'):
            ik.lim_y_min = rot.y

        elif self.mode in ('MIN_Z'):
            ik.lim_z_min = rot.z

        elif self.mode in ('MIN_XYZ'):
            ik.lim_x_min = rot.x
            ik.lim_y_min = rot.y
            ik.lim_z_min = rot.z

        # set max limits
        elif self.mode in ('MAX_X'):
            ik.lim_x_max = rot.x

        elif self.mode in ('MAX_Y'):
            ik.lim_y_max = rot.y

        elif self.mode == 'MAX_Z':
            ik.lim_z_max = rot.z

        elif self.mode in ('MAX_XYZ'):
            ik.lim_x_max = rot.x
            ik.lim_y_max = rot.y
            ik.lim_z_max = rot.z

        # set min/max limits
        elif self.mode == 'MIN_MAX_X':
            ik.lim_x_min = -rot.x
            ik.lim_x_max = rot.x

        elif self.mode == 'MIN_MAX_Y':
            ik.lim_y_min = -rot.y
            ik.lim_y_max = rot.y

        elif self.mode == 'MIN_MAX_Z':
            ik.lim_z_min = -rot.z
            ik.lim_z_max = rot.z

        utils.draw.redraw_areas()
        self.report({'INFO'}, text.get_text(text.warn.ready))

        return {'FINISHED'}


classes = (
    XRAY_OT_convert_limits_to_constraints,
    XRAY_OT_remove_limits_constraints,
    XRAY_OT_convert_ik_to_xray_limits,
    XRAY_OT_convert_xray_to_ik_limits,
    XRAY_OT_clear_ik_limits,
    XRAY_OT_set_joint_limits
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
