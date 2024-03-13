# blender modules
import bpy
import bl_operators

# addon modules
from . import props
from .. import utils


class XRAY_MT_prefs_presets(bpy.types.Menu):
    bl_label = 'Settings Presets'
    preset_subdir = 'io_scene_xray/preferences'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset


class XRAY_OT_add_prefs_preset(
        bl_operators.presets.AddPresetBase,
        utils.ie.BaseOperator
    ):

    bl_idname = 'io_scene_xray.prefs_preset_add'
    bl_label = 'Add X-Ray Preferences Preset'
    preset_menu = 'XRAY_MT_prefs_presets'
    preset_subdir = 'io_scene_xray/preferences'

    if utils.version.IS_28:
        preset_defines = [
            'prefs = bpy.context.preferences.'
            'addons["io_scene_xray"].preferences',
        ]
    else:
        preset_defines = [
            'prefs = bpy.context.user_preferences.'
            'addons["io_scene_xray"].preferences',
        ]

    preset_values = []

    for prop_key in props.prefs_props.keys():
        preset_values.append('prefs.{}'.format(prop_key))

    for prop_key in props.custom_props.keys():
        preset_values.append('prefs.custom_props.{}'.format(prop_key))


classes = (
    XRAY_MT_prefs_presets,
    XRAY_OT_add_prefs_preset
)


def register():
    for clas in classes:
        bpy.utils.register_class(clas)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
