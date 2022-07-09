# standart modules
import math

# blender modules
import bpy

# addon modules
from .. import utils
from .. import version_utils


def _get_real_bone_shape():
    result = bpy.data.objects.get('real_bone_shape')
    if result is None:
        result = bpy.data.objects.new('real_bone_shape', None)
        version_utils.set_empty_draw_type(result, 'SPHERE')
    return result


op_props = {
    'mode': bpy.props.EnumProperty(
        name='Mode',
        items=(
            ('ADAPTIVE', 'Adaptive', ''),
            ('CONSTANT', 'Constant', '')
        ),
        default='ADAPTIVE'
    ),
    'size': bpy.props.FloatProperty(
        name='Bone Size', default=0.05, min=0.0001, max=1000.0, precision=4
    ),
    'custom_shapes': bpy.props.BoolProperty(
        name='Custom Shapes', default=False
    )
}


class XRAY_OT_resize_bones(bpy.types.Operator):
    bl_idname = 'io_scene_xray.resize_bones'
    bl_label = 'Resize Bones'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        row = column.row(align=True)
        row.prop(self, 'mode', expand=True)
        row = column.row(align=True)
        row.active = self.mode == 'CONSTANT'
        row.prop(self, 'size')
        column.prop(self, 'custom_shapes', toggle=True)

    @utils.set_cursor_state
    def execute(self, context):
        edited_count = 0
        active_object = context.active_object
        for obj in context.selected_objects:
            status = self.resize_bones(obj)
            if status:
                edited_count += 1
        version_utils.set_active_object(active_object)
        self.report({'INFO'}, 'Edited {0} objects'.format(edited_count))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def get_bones_length(self, bones):
        lenghts = [0] * len(bones)
        for index_0, bone_0 in enumerate(bones):
            min_rad_sq = math.inf
            for index_1, bone_1 in enumerate(bones):
                if index_1 == index_0:
                    continue
                rad_sq = (bone_1.head - bone_0.head).length_squared
                if rad_sq < min_rad_sq:
                    min_rad_sq = rad_sq
            lenghts[index_0] = math.sqrt(min_rad_sq)
        return lenghts

    def resize_bones(self, obj):
        correct_context = False
        if obj:
            if obj.type == 'ARMATURE':
                correct_context = True
        if not correct_context:
            return False
        version_utils.set_active_object(obj)
        mode = obj.mode
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bpy_armature = obj.data
            bones = bpy_armature.edit_bones
            if self.mode == 'ADAPTIVE':
                lenghts = self.get_bones_length(bones)
                for bone, length in zip(bones, lenghts):
                    bone.length = min(max(length * 0.4, 0.01), 0.1)
            else:
                lenghts = [self.size] * len(bones)
                for bone, length in zip(bones, lenghts):
                    bone.length = length
            bpy.ops.object.mode_set(mode='POSE')
            if self.custom_shapes:
                for pose_bone in obj.pose.bones:
                    pose_bone.custom_shape = _get_real_bone_shape()
            else:
                for pose_bone in obj.pose.bones:
                    pose_bone.custom_shape = None
        finally:
            bpy.ops.object.mode_set(mode=mode)
        return True


classes = (
    XRAY_OT_resize_bones,
)


def register():
    version_utils.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
