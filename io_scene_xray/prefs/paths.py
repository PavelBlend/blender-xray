# blender modules
import bpy

# addon modules
from . import props
from .. import utils
from .. import formats


def draw_paths_list_elements(layout):
    layout.operator(
        ops.motion.XRAY_OT_add_all_actions.bl_idname,
        text='',
        icon='ACTION'
    )


path_settings_props = {
    'name': bpy.props.StringProperty(),
    'sdk_ver': formats.ie.PropSDKVersion()
}

path_settings_props.update(props.paths_props)


class PathsSettings(bpy.types.PropertyGroup):
    props = path_settings_props

    if not utils.version.IS_28:
        for prop_name, prop_value in path_settings_props.items():
            exec('{0} = path_settings_props.get("{0}")'.format(prop_name))


class XRAY_UL_path_presets_list(bpy.types.UIList):
    bl_idname = 'XRAY_UL_path_presets_list'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if data.paths_presets_index == index:
            icon = 'CHECKBOX_HLT'
        else:
            icon = 'CHECKBOX_DEHLT'

        row = layout.row()
        row.label(text='', icon=icon)

        layout.prop(item, 'name', text='')


path_configs_props = {
    'name': bpy.props.StringProperty(),
    'platform': bpy.props.StringProperty(),
    'mod': bpy.props.StringProperty()
}


class PathsConfigs(bpy.types.PropertyGroup):
    props = path_configs_props

    if not utils.version.IS_28:
        for prop_name, prop_value in path_configs_props.items():
            exec('{0} = path_configs_props.get("{0}")'.format(prop_name))


class XRAY_UL_path_configs_list(bpy.types.UIList):
    bl_idname = 'XRAY_UL_path_configs_list'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if data.paths_configs_index == index:
            icon = 'CHECKBOX_HLT'
        else:
            icon = 'CHECKBOX_DEHLT'

        row = layout.row()
        row.label(text='', icon=icon)

        layout.prop(item, 'name', text='')


path_presets_props = {
    'paths_presets': bpy.props.CollectionProperty(type=PathsSettings),
    'paths_presets_index': bpy.props.IntProperty(),

    'paths_configs': bpy.props.CollectionProperty(type=PathsConfigs),
    'paths_configs_index': bpy.props.IntProperty()
}
props.plugin_preferences_props.update(path_presets_props)


classes = (
    PathsSettings,
    PathsConfigs,
    XRAY_UL_path_presets_list,
    XRAY_UL_path_configs_list,
)


def register():
    utils.version.register_operators(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)