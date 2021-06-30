import bpy

from . import utils


class XRAY_OT_ResetPreferencesSettings(bpy.types.Operator):
    bl_idname = 'io_scene_xray.reset_preferences_settings'
    bl_label = 'Reset All Settings'

    def execute(self, _context):
        prefs = utils.get_preferences()
        # reset main settings
        for prop_name in prefs.utils.plugin_preferences_props.keys():
            prefs.property_unset(prop_name)
        # reset custom properties settings
        for prop_name in xray_custom_properties.keys():
            prefs.custom_props.property_unset(prop_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


def register():
    bpy.utils.register_class(XRAY_OT_ResetPreferencesSettings)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_ResetPreferencesSettings)
