# standart modules
import math

# blender modules
import bpy

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
    bl_label = 'Copy'

    def execute(self, context):
        if not context.object:
            return {'FINISHED'}
        else:
            write_buffer_data()
            return {'FINISHED'}
