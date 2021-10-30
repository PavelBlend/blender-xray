# blender modules
import bpy

# addon modules
from . import prefs
from . import version_utils


class XRAY_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    if not version_utils.IS_28:
        for prop_name, prop_value in prefs.props.plugin_preferences_props.items():
            exec('{0} = prefs.props.plugin_preferences_props.get("{0}")'.format(prop_name))


    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.menu(
            prefs.preset.XRAY_MT_prefs_presets.__name__,
            text=prefs.preset.XRAY_MT_prefs_presets.bl_label
        )
        row.operator(
            prefs.preset.XRAY_OT_add_prefs_preset.bl_idname,
            text='',
            icon=version_utils.get_icon('ZOOMIN')
        )
        row.operator(
            prefs.preset.XRAY_OT_add_prefs_preset.bl_idname,
            text='',
            icon=version_utils.get_icon('ZOOMOUT')
        ).remove_active = True

        layout.row().prop(self, 'category', expand=True)

        if self.category == 'PATHS':
            prefs.ui.draw_paths(self)

        elif self.category == 'DEFAULTS':
            prefs.ui.draw_defaults(self)

        elif self.category == 'PLUGINS':
            prefs.ui.draw_operators_enable_disable(self)

        elif self.category == 'KEYMAP':
            prefs.ui.draw_keymaps(context, self)

        elif self.category == 'CUSTOM_PROPS':
            prefs.ui.draw_custom_props(self)

        elif self.category == 'OTHERS':
            prefs.ui.draw_others(self)

        split = version_utils.layout_split(layout, 0.6)
        split.label(text='')
        split.operator(
            prefs.ops.XRAY_OT_reset_prefs_settings.bl_idname, icon='CANCEL'
        )


def register():
    prefs.register()
    version_utils.assign_props([
        (prefs.props.plugin_preferences_props, XRAY_addon_preferences),
    ])
    bpy.utils.register_class(XRAY_addon_preferences)


def unregister():
    bpy.utils.unregister_class(XRAY_addon_preferences)
    prefs.unregister()
