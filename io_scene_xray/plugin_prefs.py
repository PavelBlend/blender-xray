# pylint: disable=C0103
from os import path

import bpy

from . import registry, xray_ltx
from .details import props as details_props
from .obj.imp import props as obj_imp_props
from .skl import props as skl_props
from .bones import props as bones_props
from .omf import props as omf_props
from .obj.exp import props as obj_exp_props
from .ui import collapsible
from .version_utils import IS_28, assign_props, get_icon, layout_split
from bl_operators.presets import AddPresetBase


def get_preferences():
    if IS_28:
        return bpy.context.preferences.addons['io_scene_xray'].preferences
    else:
        return bpy.context.user_preferences.addons['io_scene_xray'].preferences


def PropSDKVersion():
    return bpy.props.EnumProperty(
        name='SDK Version',
        items=(('soc', 'SoC', ''), ('cscop', 'CS/CoP', ''))
    )


def PropAnmCameraAnimation():
    return bpy.props.BoolProperty(
        name='Create Linked Camera',
        description='Create animated camera object (linked to "empty"-object)',
        default=True
    )


def PropUseExportPaths():
    return bpy.props.BoolProperty(
        name='Use Export Paths',
        description='Append the Object.ExportPath to the export directory for each object',
        default=True
    )


__AUTO_PROPS__ = [
    'gamedata_folder',
    'textures_folder',
    'gamemtl_file',
    'eshader_file',
    'cshader_file',
    'objects_folder'
]
fs_props = {
    'gamedata_folder': ('$game_data$', None),
    'textures_folder': ('$game_textures$', None),
    'gamemtl_file': ('$game_data$', 'gamemtl.xr'),
    'eshader_file': ('$game_data$', 'shaders.xr'),
    'cshader_file': ('$game_data$', 'shaders_xrlc.xr'),
    'objects_folder': ('$objects$', None)
}
def _auto_path(prefs, self_name, path_suffix, checker):
    if prefs.fs_ltx_file:
        if not path.exists(prefs.fs_ltx_file):
            return ''
        try:
            fs = xray_ltx.StalkerLtxParser(prefs.fs_ltx_file)
        except:
            print('Invalid fs.ltx syntax')
            return ''
        prop_key, file_name = fs_props[self_name]
        dir_path = fs.values[prop_key]
        if file_name:
            result = path.join(dir_path, file_name)
        else:
            result = dir_path
        return result
    for prop in __AUTO_PROPS__:
        if prop == self_name:
            continue
        value = getattr(prefs, prop)
        if not value:
            continue
        if prop == 'objects_folder':
            continue
        result = path.normpath(value)
        if prop != 'gamedata_folder':
            dirname = path.dirname(result)
            if dirname == result:
                continue  # path.dirname('T:') == 'T:'
            result = dirname
        if path_suffix:
            result = path.join(result, path_suffix)
            if self_name == 'objects_folder':
                result = path.abspath(result)
        if checker(result):
            return result
    return ''


def update_menu_func(self, context):
    from . import plugin
    plugin.append_menu_func()


_explicit_path_op_props = {
    'path': bpy.props.StringProperty(),
}


def build_auto_id(prop):
    return prop + '_auto'


@registry.module_thing
class _ExplicitPathOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.explicit_path'
    bl_label = 'Make Explicit'
    bl_description = 'Make this path explicit using the automatically calculated value'

    if not IS_28:
        for prop_name, prop_value in _explicit_path_op_props.items():
            exec('{0} = _explicit_path_op_props.get("{0}")'.format(prop_name))

    def execute(self, _context):
        prefs = get_preferences()
        auto_prop = build_auto_id(self.path)
        value = getattr(prefs, auto_prop)
        setattr(prefs, self.path, value)
        setattr(prefs, auto_prop, '')
        return {'FINISHED'}


def update_keymap(self, context):
    from . import hotkeys

    keymaps, keymap_item = hotkeys.io_scene_xray_keymaps[hotkeys.obj_imp_keymap.operator_id]
    keymap_item.type = self.import_object_key
    keymap_item.shift = self.import_object_shift

    keymaps, keymap_item = hotkeys.io_scene_xray_keymaps[hotkeys.obj_exp_keymap.operator_id]
    keymap_item.type = self.export_object_key
    keymap_item.shift = self.export_object_shift


key_items = (
    ('F5', 'F5', ''),
    ('F6', 'F6', ''),
    ('F7', 'F7', ''),
    ('F8', 'F8', ''),
    ('F9', 'F9', ''),
)


path_props_suffix_values = {
    'gamedata_folder': '',
    'textures_folder': 'textures',
    'gamemtl_file': 'gamemtl.xr',
    'eshader_file': 'shaders.xr',
    'cshader_file': 'shaders_xrlc.xr',
    'objects_folder': path.join('..', 'rawdata', 'objects')
}
FILE = 'FILE'
DIRECTORY = 'DIRECTORY'
path_props_types = {
    'gamedata_folder': DIRECTORY,
    'textures_folder': DIRECTORY,
    'gamemtl_file': FILE,
    'eshader_file': FILE,
    'cshader_file': FILE,
    'objects_folder': DIRECTORY
}


def update_paths(prefs, context):
    for path_prop, suffix in path_props_suffix_values.items():
        if getattr(prefs, path_prop):
            setattr(prefs, build_auto_id(path_prop), getattr(prefs, path_prop))
            continue
        prop_type = path_props_types[path_prop]
        if prop_type == DIRECTORY:
            cheker_function = path.isdir
        elif prop_type == FILE:
            cheker_function = path.isfile
        path_value = _auto_path(prefs, path_prop, suffix, cheker_function)
        setattr(prefs, build_auto_id(path_prop), path_value)


category_items = (
    ('PATHS', 'Paths', ''),
    ('DEFAULTS', 'Defaults', ''),
    ('PLUGINS', 'Plugins', ''),
    ('KEYMAP', 'Keymap', ''),
    ('OTHERS', 'Others', '')
)
plugin_preferences_props = {
    # path props
    'fs_ltx_file': bpy.props.StringProperty(
        subtype='FILE_PATH', name='fs.ltx File', update=update_paths
    ),
    'gamedata_folder': bpy.props.StringProperty(subtype='DIR_PATH', update=update_paths),
    'textures_folder': bpy.props.StringProperty(subtype='DIR_PATH', update=update_paths),
    'gamemtl_file': bpy.props.StringProperty(subtype='FILE_PATH', update=update_paths),
    'eshader_file': bpy.props.StringProperty(subtype='FILE_PATH', update=update_paths),
    'cshader_file': bpy.props.StringProperty(subtype='FILE_PATH', update=update_paths),
    'objects_folder': bpy.props.StringProperty(subtype='DIR_PATH', update=update_paths),
    # path auto props
    'gamedata_folder_auto': bpy.props.StringProperty(),
    'textures_folder_auto': bpy.props.StringProperty(),
    'gamemtl_file_auto': bpy.props.StringProperty(),
    'eshader_file_auto': bpy.props.StringProperty(),
    'cshader_file_auto': bpy.props.StringProperty(),
    'objects_folder_auto': bpy.props.StringProperty(),

    'expert_mode': bpy.props.BoolProperty(
        name='Expert Mode', description='Show additional properties/controls'
    ),
    'compact_menus': bpy.props.BoolProperty(
        name='Compact Import/Export Menus', update=update_menu_func
    ),
    'sdk_version': PropSDKVersion(),
    'object_motions_import': obj_imp_props.PropObjectMotionsImport(),
    'object_motions_export': obj_exp_props.PropObjectMotionsExport(),
    'object_mesh_split_by_mat': obj_imp_props.PropObjectMeshSplitByMaterials(),
    'object_texture_names_from_path': obj_exp_props.PropObjectTextureNamesFromPath(),
    'smoothing_out_of': obj_exp_props.prop_smoothing_out_of(),
    'object_bones_custom_shapes': obj_imp_props.PropObjectBonesCustomShapes(),
    'use_motion_prefix_name': obj_imp_props.PropObjectUseMotionPrefixName(),
    'anm_create_camera': PropAnmCameraAnimation(),
    # details import props
    'details_models_in_a_row': details_props.prop_details_models_in_a_row(),
    'load_slots': details_props.prop_details_load_slots(),
    'details_format': details_props.prop_details_format(),
    # details export props
    'format_version': details_props.prop_details_format_version(),
    # skl props
    'add_actions_to_motion_list': skl_props.prop_skl_add_actions_to_motion_list(),
    # bones props
    'bones_import_bone_parts': omf_props.prop_import_bone_parts(),
    'bones_import_bone_properties': bones_props.prop_import_bone_properties(),
    'bones_export_bone_parts': omf_props.prop_export_bone_parts(),
    'bones_export_bone_properties': bones_props.prop_export_bone_properties(),
    # omf props
    'import_bone_parts': omf_props.prop_import_bone_parts(),
    'omf_export_bone_parts': omf_props.prop_export_bone_parts(),
    'omf_export_mode': omf_props.prop_omf_export_mode(),
    # keymap
    'import_object_key': bpy.props.EnumProperty(
        default='F8', update=update_keymap, items=key_items,
        name='Import Object Key'
    ),
    'import_object_shift': bpy.props.BoolProperty(
        default=False, update=update_keymap
    ),
    'export_object_key': bpy.props.EnumProperty(
        default='F8', update=update_keymap, items=key_items,
        name='Export Object Key'
    ),
    'export_object_shift': bpy.props.BoolProperty(
        default=True, update=update_keymap
    ),
    # enable import plugins
    'enable_object_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_anm_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_dm_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_details_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_skls_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_bones_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_err_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_level_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_game_level_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_omf_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    # enable export plugins
    'enable_object_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_anm_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_dm_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_details_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_skls_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_bones_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_level_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_game_level_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_omf_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_ogf_export': bpy.props.BoolProperty(default=True, update=update_menu_func),

    'category': bpy.props.EnumProperty(default='PATHS', items=category_items)
}


path_props_names = {
    'fs_ltx_file': 'fs.ltx File',
    'gamedata_folder': 'Gamedata Folder',
    'textures_folder': 'Textures Folder',
    'gamemtl_file': 'GameMtl File',
    'eshader_file': 'EShader File',
    'cshader_file': 'CShader File',
    'objects_folder': 'Objects Folder'
}


@registry.module_thing
class PluginPreferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    if not IS_28:
        for prop_name, prop_value in plugin_preferences_props.items():
            exec('{0} = plugin_preferences_props.get("{0}")'.format(prop_name))

    def get_split(self, layout):
        return layout_split(layout, 0.3)

    def draw_path_prop(self, prop):
        layout = self.layout
        split = self.get_split(layout)
        split.label(text=path_props_names[prop] + ':')
        auto_prop = build_auto_id(prop)
        if getattr(self, auto_prop):
            row = split.row(align=True)
            row_prop = row.row(align=True)
            row_prop.enabled = False
            row_prop.prop(self, auto_prop, text='')
            operator = row.operator(_ExplicitPathOp.bl_idname, icon='MODIFIER', text='')
            operator.path = prop
        else:
            split.prop(self, prop, text='')

    def draw(self, _context):

        def prop_bool(layout, data, prop):
            layout.prop(data, prop)

        layout = self.layout

        row = layout.row(align=True)
        row.menu(PREFS_MT_xray_presets.__name__, text=PREFS_MT_xray_presets.bl_label)
        row.operator(AddPresetXrayPrefs.bl_idname, text='', icon=get_icon('ZOOMIN'))
        row.operator(AddPresetXrayPrefs.bl_idname, text='', icon=get_icon('ZOOMOUT')).remove_active = True

        layout.row().prop(self, 'category', expand=True)

        if self.category == 'PATHS':
            split = self.get_split(layout)
            split.label(text=path_props_names['fs_ltx_file'] + ':')
            split.prop(self, 'fs_ltx_file', text='')
            self.draw_path_prop('gamedata_folder')
            self.draw_path_prop('textures_folder')
            self.draw_path_prop('gamemtl_file')
            self.draw_path_prop('eshader_file')
            self.draw_path_prop('cshader_file')
            self.draw_path_prop('objects_folder')
        elif self.category == 'DEFAULTS':
            _, box_n = collapsible.draw(layout, 'plugin_prefs:defaults.common', 'Common', style='tree')
            if box_n:
                row = box_n.row()
                row.label(text='SDK Version:')
                row.prop(self, 'sdk_version', expand=True)
                box_n.prop(self, 'object_texture_names_from_path')
                box_n.prop(self, 'use_motion_prefix_name')

            _, box_n = collapsible.draw(layout, 'plugin_prefs:defaults.object', 'Source Object (.object)', style='tree')
            if box_n:
                box_n.label(text='Import:')
                prop_bool(box_n, self, 'object_motions_import')
                prop_bool(box_n, self, 'object_mesh_split_by_mat')
                prop_bool(box_n, self, 'object_bones_custom_shapes')
                box_n.label(text='Export:')
                prop_bool(box_n, self, 'object_motions_export')
                row = box_n.row()
                row.label(text='Smoothing Out of:')
                row.prop(self, 'smoothing_out_of', text='')

            _, box_n = collapsible.draw(layout, 'plugin_prefs:defaults.skl', 'Skeletal Animation (.skl, .skls)', style='tree')
            if box_n:
                prop_bool(box_n, self, 'add_actions_to_motion_list')

            _, box_n = collapsible.draw(layout, 'plugin_prefs:defaults.bones', 'Bones Data (.bones)', style='tree')
            if box_n:
                box_n.label(text='Import:')
                prop_bool(box_n, self, 'bones_import_bone_properties')
                prop_bool(box_n, self, 'bones_import_bone_parts')
                box_n.label(text='Export:')
                prop_bool(box_n, self, 'bones_export_bone_properties')
                prop_bool(box_n, self, 'bones_export_bone_parts')

            _, box_n = collapsible.draw(layout, 'plugin_prefs:defaults.anm', 'Animation (.anm)', style='tree')
            if box_n:
                prop_bool(box_n, self, 'anm_create_camera')

            _, box_n = collapsible.draw(layout, 'plugin_prefs:defaults.details', 'Details (.dm, .details)', style='tree')
            if box_n:
                box_n.label(text='Import:')
                prop_bool(box_n, self, 'details_models_in_a_row')
                prop_bool(box_n, self, 'load_slots')
                row = box_n.row()
                row.prop(self, 'details_format', expand=True)
                box_n.label(text='Export:')
                row = box_n.row()
                row.prop(self, 'format_version', expand=True)

            _, box_n = collapsible.draw(layout, 'plugin_prefs:defaults.omf', 'Game Motion (.omf)', style='tree')
            if box_n:
                box_n.label(text='Import:')
                prop_bool(box_n, self, 'import_bone_parts')
                box_n.label(text='Export:')
                prop_bool(box_n, self, 'omf_export_bone_parts')
                row = box_n.row()
                row.prop(self, 'omf_export_mode', expand=True)

        elif self.category == 'PLUGINS':
            row = layout.row()

            column_1 = row.column()
            column_2 = row.column()

            column_1.label(text='Import Plugins:')
            column_1.prop(self, 'enable_object_import', text='*.object')
            column_1.prop(self, 'enable_anm_import', text='*.anm')
            column_1.prop(self, 'enable_dm_import', text='*.dm')
            column_1.prop(self, 'enable_details_import', text='*.details')
            column_1.prop(self, 'enable_skls_import', text='*.skls')
            column_1.prop(self, 'enable_bones_import', text='*.bones')
            column_1.prop(self, 'enable_level_import', text='*.level')
            column_1.prop(self, 'enable_omf_import', text='*.omf')
            if IS_28:
                column_1.prop(self, 'enable_game_level_import', text='level')
            column_1.prop(self, 'enable_err_import', text='*.err')

            column_2.label(text='Export Plugins:')
            column_2.prop(self, 'enable_object_export', text='*.object')
            column_2.prop(self, 'enable_anm_export', text='*.anm')
            column_2.prop(self, 'enable_dm_export', text='*.dm')
            column_2.prop(self, 'enable_details_export', text='*.details')
            column_2.prop(self, 'enable_skls_export', text='*.skls')
            column_2.prop(self, 'enable_bones_export', text='*.bones')
            column_2.prop(self, 'enable_level_export', text='*.level')
            column_2.prop(self, 'enable_omf_export', text='*.omf')
            if IS_28:
                column_2.prop(self, 'enable_game_level_export', text='level')
            column_2.prop(self, 'enable_ogf_export', text='*.ogf')

        elif self.category == 'KEYMAP':
            row = layout.row()
            row.label(text='Import Object:')
            row.prop(self, 'import_object_key', text='')
            row.prop(self, 'import_object_shift', text='Shift', toggle=True)

            row = layout.row()
            row.label(text='Export Object:')
            row.prop(self, 'export_object_key', text='')
            row.prop(self, 'export_object_shift', text='Shift', toggle=True)

        elif self.category == 'OTHERS':
            prop_bool(layout, self, 'expert_mode')
            prop_bool(layout, self, 'compact_menus')


assign_props([
    (_explicit_path_op_props, _ExplicitPathOp),
])
assign_props([
    (plugin_preferences_props, PluginPreferences),
])


@registry.module_thing
class PREFS_MT_xray_presets(bpy.types.Menu):
    bl_label = 'Settings Presets'
    preset_subdir = 'io_scene_xray/preferences'
    preset_operator = 'script.execute_preset'
    draw = bpy.types.Menu.draw_preset


@registry.module_thing
class AddPresetXrayPrefs(AddPresetBase, bpy.types.Operator):
    bl_idname = 'xray.prefs_preset_add'
    bl_label = 'Add XRay Preferences Preset'
    preset_menu = 'PREFS_MT_xray_presets'

    preset_defines = [
        'prefs = bpy.context.preferences.addons["io_scene_xray"].preferences'
    ]
    preset_values = []
    for prop_key in plugin_preferences_props.keys():
        preset_values.append('prefs.{}'.format(prop_key))
    for auto_prop_key in __AUTO_PROPS__:
        preset_values.append('prefs.{}'.format(auto_prop_key))
        preset_values.append('prefs.{}_auto'.format(auto_prop_key))
    preset_subdir = 'io_scene_xray/preferences'
