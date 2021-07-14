import bpy

from .. import version_utils


def get_preferences():
    if version_utils.IS_28:
        return bpy.context.preferences.addons['io_scene_xray'].preferences
    else:
        return bpy.context.user_preferences.addons['io_scene_xray'].preferences
