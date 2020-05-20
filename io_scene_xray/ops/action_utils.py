import os

import bpy

from .. import xray_io


BUFFER_FILE_NAME = 'blender-xray-buffer-file.bin'
ACTION_SETTINGS_HEADER = 'ACTION_SETTINGS'


def get_xray_settings():
    obj = bpy.context.object
    if not obj:
        return
    anim_data = obj.animation_data
    if anim_data:
        action = anim_data.action
        xray = action.xray
        return xray


def write_buffer_data():
    folder = get_temp_folder()
    filepath = os.path.join(folder, BUFFER_FILE_NAME)
    packed_writer = xray_io.PackedWriter()
    xray = get_xray_settings()
    if xray:
        packed_writer.puts(ACTION_SETTINGS_HEADER)
        packed_writer.putf('<f', xray.fps)
        packed_writer.putf('<I', xray.flags)
        packed_writer.putf('<f', xray.speed)
        packed_writer.putf('<f', xray.accrue)
        packed_writer.putf('<f', xray.falloff)
        packed_writer.putf('<f', xray.power)
        packed_writer.puts(xray.bonepart_name)
        packed_writer.puts(xray.bonestart_name)
    with open(filepath, 'wb') as file:
        file.write(packed_writer.data)


def read_buffer_data():
    folder = get_temp_folder()
    filepath = os.path.join(folder, BUFFER_FILE_NAME)
    if not os.path.exists(filepath):
        return
    xray = get_xray_settings()
    if xray:
        with open(filepath, 'rb') as file:
            data = file.read()
        packed_reader = xray_io.PackedReader(data)
        header = packed_reader.gets()
        if header == ACTION_SETTINGS_HEADER:
            xray.fps = packed_reader.getf('<f')[0]
            xray.flags = packed_reader.getf('<I')[0]
            xray.speed = packed_reader.getf('<f')[0]
            xray.accrue = packed_reader.getf('<f')[0]
            xray.falloff = packed_reader.getf('<f')[0]
            xray.power = packed_reader.getf('<f')[0]
            xray.bonepart_name = packed_reader.gets()
            xray.bonestart_name = packed_reader.gets()


def get_temp_folder():
    context = bpy.context
    prefs = context.preferences
    filepaths = prefs.filepaths
    temp_folder = bpy.path.abspath(filepaths.temporary_directory)
    return temp_folder


class XRayCopyActionSettingsOperator(bpy.types.Operator):
    bl_idname = 'io_scene_xray.copy_action_settings'
    bl_label = 'Copy'

    def execute(self, context):
        write_buffer_data()
        return {'FINISHED'}


class XRayPasteActionSettingsOperator(bpy.types.Operator):
    bl_idname = 'io_scene_xray.paste_action_settings'
    bl_label = 'Paste'

    def execute(self, context):
        read_buffer_data()
        return {'FINISHED'}
