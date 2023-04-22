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
        for prop_name in props.plugin_preferences_props:
            prefs.property_unset(prop_name)
        # reset custom properties settings
        for prop_name in props.xray_custom_properties:
            prefs.custom_props.property_unset(prop_name)
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        return context.window_manager.invoke_confirm(self, event)


op_props = {
    'path': bpy.props.StringProperty(),
}


class XRAY_OT_explicit_path(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.explicit_path'
    bl_label = 'Make Explicit'
    bl_description = 'Make this path explicit using the automatically calculated value'

    props = op_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def execute(self, context):
        preferences = utils.version.get_preferences()
        auto_prop = props.build_auto_id(self.path)
        value = getattr(preferences, auto_prop)
        setattr(preferences, self.path, value)
        setattr(preferences, auto_prop, '')
        return {'FINISHED'}


classes = (
    XRAY_OT_explicit_path,
    XRAY_OT_reset_prefs_settings
)


def register():
    utils.version.register_operators(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
