# blender modules
import bpy

# addon modules
from . import ui
from . import ops
from . import paths
from . import props
from . import preset
from .. import utils


class XRAY_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    for prop_name in props.prefs_props.keys():
        exec('{0} = props.prefs_props.get("{0}")'.format(prop_name))

    use_update = bpy.props.BoolProperty(default=True)
    custom_props = bpy.props.PointerProperty(type=props.XRayPrefsCustomProperties)

    # paths
    paths_presets = bpy.props.CollectionProperty(type=paths.PathsSettings)
    paths_presets_index = bpy.props.IntProperty()

    paths_configs = bpy.props.CollectionProperty(type=paths.PathsConfigs)
    paths_configs_index = bpy.props.IntProperty()

    used_config = bpy.props.StringProperty()

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
    utils.version.register_classes(XRAY_addon_preferences)


def unregister():
    bpy.utils.unregister_class(XRAY_addon_preferences)
