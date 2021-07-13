import bpy

from . import utils, props
from .. import version_utils


class XRAY_OT_ResetPreferencesSettings(bpy.types.Operator):
    bl_idname = 'io_scene_xray.reset_preferences_settings'
    bl_label = 'Reset All Settings'

    def execute(self, _context):
        prefs = utils.get_preferences()
        # reset main settings
        for prop_name in props.plugin_preferences_props.keys():
            prefs.property_unset(prop_name)
        # reset custom properties settings
        for prop_name in props.xray_custom_properties.keys():
            prefs.custom_props.property_unset(prop_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


_explicit_path_op_props = {
    'path': bpy.props.StringProperty(),
}


class _ExplicitPathOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.explicit_path'
    bl_label = 'Make Explicit'
    bl_description = 'Make this path explicit using the automatically calculated value'

    if not version_utils.IS_28:
        for prop_name, prop_value in _explicit_path_op_props.items():
            exec('{0} = _explicit_path_op_props.get("{0}")'.format(prop_name))

    def execute(self, _context):
        preferences = utils.get_preferences()
        auto_prop = props.build_auto_id(self.path)
        value = getattr(preferences, auto_prop)
        setattr(preferences, self.path, value)
        setattr(preferences, auto_prop, '')
        return {'FINISHED'}


classes = (
    _ExplicitPathOp,
    XRAY_OT_ResetPreferencesSettings
)


def register():
    version_utils.assign_props([
        (_explicit_path_op_props, _ExplicitPathOp),
    ])
    for clas in classes:
        bpy.utils.register_class(clas)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
