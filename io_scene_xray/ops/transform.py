# standart modules
import math

# blender modules
import bpy
import mathutils

# addon modules
from .. import utils
from .. import text


def get_object_transforms():
    # get blender transforms
    obj = bpy.context.active_object
    translation = obj.location
    if obj.rotation_mode == 'QUATERNION':
        rotation = obj.rotation_quaternion.to_euler('YXZ')
    else:
        rotation = obj.rotation_euler.to_matrix().to_euler('YXZ')
    # convert to x-ray engine transforms
    xray_translation = (translation[0], translation[2], translation[1])
    xray_rotation = (rotation[2], rotation[0], rotation[1])
    return xray_translation, xray_rotation


def write_buffer_data():
    xray_translation, xray_rotation = get_object_transforms()
    buffer_text = ''
    buffer_text += '; hud transforms\n'
    buffer_text += 'position = {:.6f}, {:.6f}, {:.6f}\n'.format(*xray_translation)
    buffer_text += 'orientation = {:.6f}, {:.6f}, {:.6f}\n'.format(
        math.degrees(xray_rotation[0]),
        math.degrees(xray_rotation[1]),
        math.degrees(xray_rotation[2])
    )
    buffer_text += '\n; hud offset\n'
    buffer_text += 'zoom_offset = {:.6f}, {:.6f}, {:.6f}\n'.format(*xray_translation)
    buffer_text += 'zoom_rotate_x = {:.6f}\n'.format(-xray_rotation[1])
    buffer_text += 'zoom_rotate_y = {:.6f}\n'.format(-xray_rotation[0])
    bpy.context.window_manager.clipboard = buffer_text


class XRAY_OT_copy_xray_tranforms(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.copy_xray_transforms'
    bl_label = 'Copy X-Ray Transforms'

    def execute(self, context):
        if not context.active_object:
            return {'FINISHED'}

        write_buffer_data()
        self.report({'INFO'}, text.get_text(text.warn.ready))
        return {'FINISHED'}


class XRAY_OT_update_xray_tranforms(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.update_xray_transforms'
    bl_label = 'Update X-Ray Transforms'
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'FINISHED'}

        xray_translation, xray_rotation = get_object_transforms()
        data = obj.xray
        data.position = xray_translation
        data.orientation = xray_rotation
        self.report({'INFO'}, text.get_text(text.warn.ready))
        return {'FINISHED'}


class XRAY_OT_update_blender_tranforms(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.update_blender_transforms'
    bl_label = 'Update Blender Transforms'
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'FINISHED'}

        if obj.rotation_mode == 'AXIS_ANGLE':
            self.report(
                {'ERROR'},
                'Object has unsupported rotation mode: {}'.format(
                    obj.rotation_mode
                )
            )
            return {'CANCELLED'}

        data = obj.xray

        # update location
        pos = data.position
        pos_mat = mathutils.Matrix.Translation((pos[0], pos[2], pos[1]))
        obj.location = pos_mat.to_translation()

        # update rotation
        rot = data.orientation
        rot_euler = mathutils.Euler((rot[1], rot[2], rot[0]), 'YXZ')

        if obj.rotation_mode == 'QUATERNION':
            obj.rotation_quaternion = rot_euler.to_quaternion()
        else:
            obj.rotation_euler = rot_euler.to_matrix().to_euler(obj.rotation_mode)

        self.report({'INFO'}, text.get_text(text.warn.ready))
        return {'FINISHED'}


classes = (
    XRAY_OT_copy_xray_tranforms,
    XRAY_OT_update_xray_tranforms,
    XRAY_OT_update_blender_tranforms
)


def register():
    for operator in classes:
        bpy.utils.register_class(operator)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
