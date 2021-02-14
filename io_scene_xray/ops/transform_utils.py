# standart modules
import math

# blender modules
import bpy, mathutils

# addon modules
from .. import registry


SECTION_NAME = 'xray_transforms'


def get_object_transforms():
    # get blender transforms
    matrix = bpy.context.object.matrix_world
    translation = matrix.to_translation()
    rotation = matrix.to_euler('YXZ')
    # convert to x-ray engine transforms
    xray_translation = (translation[0], translation[2], translation[1])
    xray_rotation = (
        math.degrees(rotation[2]),
        math.degrees(rotation[0]),
        math.degrees(rotation[1])
    )
    return xray_translation, xray_rotation


def write_buffer_data():
    xray_translation, xray_rotation = get_object_transforms()
    buffer_text = ''
    buffer_text += '[{}]\n'.format(SECTION_NAME)
    buffer_text += 'position = {}, {}, {}\n'.format(*xray_translation)
    buffer_text += 'orientation = {}, {}, {}\n'.format(*xray_rotation)
    bpy.context.window_manager.clipboard = buffer_text


@registry.module_thing
class XRAY_OT_CopyObjectTranforms(bpy.types.Operator):
    bl_idname = 'io_scene_xray.copy_object_transforms'
    bl_label = 'Copy X-Ray Transforms'

    def execute(self, context):
        if not context.object:
            return {'FINISHED'}
        else:
            write_buffer_data()
            return {'FINISHED'}


@registry.module_thing
class XRAY_OT_UpdateXRayObjectTranforms(bpy.types.Operator):
    bl_idname = 'io_scene_xray.update_xray_object_transforms'
    bl_label = 'Update X-Ray Transforms'
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object
        if not obj:
            return {'FINISHED'}
        else:
            xray_translation, xray_rotation = get_object_transforms()
            data = obj.xray
            data.position = xray_translation
            data.orientation = xray_rotation
            return {'FINISHED'}


@registry.module_thing
class XRAY_OT_UpdateBlenderObjectTranforms(bpy.types.Operator):
    bl_idname = 'io_scene_xray.update_blender_object_transforms'
    bl_label = 'Update Blender Transforms'
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object
        if not obj:
            return {'FINISHED'}
        else:
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
            rot_euler = mathutils.Euler(
                (
                    math.radians(rot[1]),
                    math.radians(rot[2]),
                    math.radians(rot[0])
                ),
                'YXZ'
            )
            if obj.rotation_mode == 'QUATERNION':
                obj.rotation_quaternion = rot_euler.to_quaternion()
            else:
                obj.rotation_euler = rot_euler.to_matrix().to_euler(obj.rotation_mode)
            return {'FINISHED'}
