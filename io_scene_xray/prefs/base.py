# blender modules
import bpy

# addon modules
from . import props
from . import ops
from . import ui
from .. import version_utils


class XRAY_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    props = props.plugin_preferences_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        ui.draw_presets(self)
        layout.row().prop(self, 'category', expand=True)
        if self.category == 'PATHS':
            ui.draw_paths(self)
        elif self.category == 'DEFAULTS':
            ui.draw_defaults(self)
        elif self.category == 'PLUGINS':
            ui.draw_formats_enable_disable(self)
        elif self.category == 'KEYMAP':
            ui.draw_keymaps(context, self)
        elif self.category == 'CUSTOM_PROPS':
            ui.draw_custom_props(self)
        elif self.category == 'OTHERS':
            ui.draw_others(self)
        split = version_utils.layout_split(layout, 0.6)
        split.label(text='')
        split.operator(
            ops.XRAY_OT_reset_prefs_settings.bl_idname, icon='CANCEL'
        )


def register():
    version_utils.register_operators(XRAY_addon_preferences)


def unregister():
    bpy.utils.unregister_class(XRAY_addon_preferences)
