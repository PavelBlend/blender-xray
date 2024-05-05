# standart modules
import math

# blender modules
import bpy

# addon modules
from .. import text
from .. import utils


def _get_real_bone_shape():
    result = bpy.data.objects.get('real_bone_shape')
    if result is None:
        result = bpy.data.objects.new('real_bone_shape', None)
        utils.version.set_empty_draw_type(result, 'SPHERE')
    return result


class XRAY_OT_resize_bones(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.resize_bones'
    bl_label = 'Resize Bones'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        name='Mode',
        items=(
            ('ADAPTIVE', 'Adaptive', ''),
            ('CONSTANT', 'Constant', '')
        ),
        default='ADAPTIVE'
    )
    change = bpy.props.EnumProperty(
        name='Change',
        items=(
            ('SELECTED', 'Selected Bones', ''),
            ('ALL', 'All Bones', '')
        ),
        default='SELECTED'
    )
    size = bpy.props.FloatProperty(
        name='Bone Size',
        default=0.05,
        min=0.0001,
        max=1000.0,
        precision=4
    )
    custom_shapes = bpy.props.BoolProperty(
        name='Custom Shapes',
        default=False
    )

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)

        column.label(text='Mode:')
        row = column.row(align=True)
        row.prop(self, 'mode', expand=True)

        row = column.row(align=True)
        row.active = self.mode == 'CONSTANT'
        row.prop(self, 'size')

        column.prop(self, 'custom_shapes', toggle=True)

        if context.mode != 'POSE':
            column.label(text='')
            column.label(
                text=text.get_tip(text.error.not_pose_mode),
                icon='ERROR'
            )

        col = column.column(align=True)
        col.label(text='Change:')
        row = col.row(align=True)
        row.prop(self, 'change', expand=True)

        if context.mode != 'POSE':
            col.active = False

    @utils.set_cursor_state
    def execute(self, context):
        edited_count = 0
        active_object = context.active_object
        for obj in context.selected_objects:
            status = self.resize_bones(obj)
            if status:
                edited_count += 1
        utils.version.set_active_object(active_object)
        self.report({'INFO'}, 'Edited {0} objects'.format(edited_count))
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def get_bones_length(self, bones, arm):
        lengths = {}
        for bone_name_1 in bones:
            bone_1 = arm.edit_bones[bone_name_1]
            min_rad_sq = math.inf
            for bone_name_2 in bones:
                bone_2 = arm.edit_bones[bone_name_2]
                if bone_name_1 == bone_name_2:
                    continue
                rad_sq = (bone_2.head - bone_1.head).length_squared
                if rad_sq < min_rad_sq:
                    min_rad_sq = rad_sq
            lengths[bone_name_1] = math.sqrt(min_rad_sq)
        return lengths

    def resize_bones(self, obj):
        correct_context = False
        if obj:
            if obj.type == 'ARMATURE':
                correct_context = True
        if not correct_context:
            return False

        utils.version.set_active_object(obj)
        mode = obj.mode
        bpy.ops.object.mode_set(mode='EDIT')

        try:
            bpy_armature = obj.data

            # collect bones
            if self.change == 'SELECTED' and mode == 'POSE':
                bones = []
                for edit_bone in bpy_armature.edit_bones:
                    bone = bpy_armature.bones[edit_bone.name]
                    if bone.select:
                        bones.append(bone.name)
            else:
                bones = [bone.name for bone in bpy_armature.bones]

            # set length
            if self.mode == 'ADAPTIVE':
                lenghts = self.get_bones_length(bones, bpy_armature)
                for bone_name in bones:
                    length = lenghts[bone_name]
                    edit_bone = bpy_armature.edit_bones[bone_name]
                    edit_bone.length = min(max(length * 0.4, 0.01), 0.1)
            else:
                for bone_name in bones:
                    edit_bone = bpy_armature.edit_bones[bone_name]
                    edit_bone.length = self.size

            # set bone shape
            bpy.ops.object.mode_set(mode='POSE')
            if self.custom_shapes:
                shape = _get_real_bone_shape()
            else:
                shape = None
            for bone_name in bones:
                pose_bone = obj.pose.bones[bone_name]
                pose_bone.custom_shape = shape

        finally:
            bpy.ops.object.mode_set(mode=mode)

        return True


classes = (
    XRAY_OT_resize_bones,
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
