# blender modules
import bpy

# addon modules
from . import ui
from . import ops
from . import props
from . import preset
from .. import utils


class XRAY_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    props = props.plugin_preferences_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        utils.draw.draw_presets(
            layout,
            preset.XRAY_MT_prefs_presets,
            preset.XRAY_OT_add_prefs_preset
        )
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

        split = utils.version.layout_split(layout, 0.6)
        split.label(text='')
        split.operator(
            ops.XRAY_OT_reset_prefs_settings.bl_idname, icon='CANCEL'
        )


def register():
    utils.version.register_operators(XRAY_addon_preferences)


def unregister():
    bpy.utils.unregister_class(XRAY_addon_preferences)
