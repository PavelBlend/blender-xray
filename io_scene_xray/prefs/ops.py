# blender modules
import bpy

# addon modules
from . import props
from .. import utils


class XRAY_OT_reset_prefs_settings(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.reset_preferences_settings'
    bl_label = 'Reset All Settings'

    def execute(self, context):
        prefs = utils.version.get_preferences()

        # reset main settings
        for prop_name in props.prefs_props.keys():
            prefs.property_unset(prop_name)

        # reset custom properties settings
        for prop_name in props.custom_props.keys():
            prefs.custom_props.property_unset(prop_name)

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        return context.window_manager.invoke_confirm(self, event)


class XRAY_OT_explicit_path(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.explicit_path'
    bl_label = 'Make Explicit'
    bl_description = 'Make this path explicit using the automatically calculated value'

    path = bpy.props.StringProperty()

    def execute(self, context):
        pref = utils.version.get_preferences()

        if pref.paths_mode == 'BASE':
            settings = pref
        else:
            settings = pref.paths_presets[pref.paths_presets_index]

        auto_prop = props.build_auto_id(self.path)

        value = getattr(settings, auto_prop)
        setattr(settings, self.path, value)
        setattr(settings, auto_prop, '')

        return {'FINISHED'}


classes = (
    XRAY_OT_explicit_path,
    XRAY_OT_reset_prefs_settings
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
