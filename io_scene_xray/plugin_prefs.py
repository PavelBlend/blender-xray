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


@registry.module_thing
class XRAY_OT_ResetPreferencesSettings(bpy.types.Operator):
    bl_idname = 'io_scene_xray.reset_preferences_settings'
    bl_label = 'Reset All Settings'

    def execute(self, _context):
        prefs = get_preferences()
        # reset main settings
        for prop_name in plugin_preferences_props.keys():
            prefs.property_unset(prop_name)
        # reset custom properties settings
        for prop_name in xray_custom_properties.keys():
            prefs.custom_props.property_unset(prop_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


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
    ('CUSTOM_PROPS', 'Custom Props', ''),
    ('OTHERS', 'Others', '')
)
custom_props_category_items = (
    ('OBJECT', 'Object', ''),
    ('MESH', 'Mesh', ''),
    ('MATERIAL', 'Material', ''),
    ('BONE', 'Bone', ''),
    ('ACTION', 'Action', '')
)
custom_props_bone_category_items = (
    ('MAIN', 'Main', ''),
    ('SHAPE', 'Shape', ''),
    ('IK', 'IK', '')
)

xray_custom_properties = {
    'category': bpy.props.EnumProperty(
        name='Custom Property Category',
        default='OBJECT',
        items=custom_props_category_items
    ),
    'bone_category': bpy.props.EnumProperty(
        name='Custom Property Bone Category',
        default='MAIN',
        items=custom_props_bone_category_items
    ),
    # object custom properties names
    'object_flags': bpy.props.StringProperty(
        name='Flags', default='flags'
    ),
    'object_userdata': bpy.props.StringProperty(
        name='Userdata', default='userdata'
    ),
    'object_lod_reference': bpy.props.StringProperty(
        name='LOD Reference', default='lod_reference'
    ),
    'object_owner_name': bpy.props.StringProperty(
        name='Owner Name', default='owner_name'
    ),
    'object_creation_time': bpy.props.StringProperty(
        name='Creation Time', default='creation_time'
    ),
    'object_modif_name': bpy.props.StringProperty(
        name='Modif Name', default='modif_name'
    ),
    'object_modified_time': bpy.props.StringProperty(
        name='Modified Time', default='modified_time'
    ),
    'object_motion_references': bpy.props.StringProperty(
        name='Motion References', default='motion_references'
    ),
    # mesh custom properties names
    'mesh_flags': bpy.props.StringProperty(
        name='Flags', default='flags'
    ),
    # material custom properties names
    'material_two_sided': bpy.props.StringProperty(
        name='Two Sided', default='two_sided'
    ),
    'material_shader': bpy.props.StringProperty(
        name='Shader', default='shader'
    ),
    'material_compile': bpy.props.StringProperty(
        name='Compile', default='compile'
    ),
    'material_game_mtl': bpy.props.StringProperty(
        name='Game Mtl', default='game_mtl'
    ),
    # bone custom properties names
    'bone_game_mtl': bpy.props.StringProperty(
        name='Game Mtl', default='game_mtl'
    ),
    'bone_length': bpy.props.StringProperty(
        name='Length', default='length'
    ),
    'bone_shape_flags': bpy.props.StringProperty(
        name='Shape Flags', default='shape_flags'
    ),
    'bone_shape_type': bpy.props.StringProperty(
        name='Shape Type', default='shape_type'
    ),
    'bone_part': bpy.props.StringProperty(
        name='Bone Part', default='bone_part'
    ),
    # box shape
    'bone_box_shape_rotation': bpy.props.StringProperty(
        name='Box Shape Rotation', default='box_shape_rotation'
    ),
    'bone_box_shape_translate': bpy.props.StringProperty(
        name='Box Shape Translate', default='box_shape_translate'
    ),
    'bone_box_shape_half_size': bpy.props.StringProperty(
        name='Box Shape Half Size', default='box_shape_half_size'
    ),
    # sphere shape
    'bone_sphere_shape_position': bpy.props.StringProperty(
        name='Sphere Shape Position', default='sphere_shape_position'
    ),
    'bone_sphere_shape_radius': bpy.props.StringProperty(
        name='Sphere Shape Radius', default='sphere_shape_radius'
    ),
    # cylinder shape
    'bone_cylinder_shape_position': bpy.props.StringProperty(
        name='Cylinder Shape Position', default='cylinder_shape_position'
    ),
    'bone_cylinder_shape_direction': bpy.props.StringProperty(
        name='Cylinder Shape Direction', default='cylinder_shape_direction'
    ),
    'bone_cylinder_shape_hight': bpy.props.StringProperty(
        name='Cylinder Shape Hight', default='cylinder_shape_hight'
    ),
    'bone_cylinder_shape_radius': bpy.props.StringProperty(
        name='Cylinder Shape Radius', default='cylinder_shape_radius'
    ),
    # ik joint type
    'bone_ik_joint_type': bpy.props.StringProperty(
        name='IK Joint Type', default='ik_joint_type'
    ),
    # limit
    'bone_limit_x_min': bpy.props.StringProperty(
        name='Limit X Min', default='limit_x_min'
    ),
    'bone_limit_x_max': bpy.props.StringProperty(
        name='Limit X Max', default='limit_x_max'
    ),
    'bone_limit_y_min': bpy.props.StringProperty(
        name='Limit Y Min', default='limit_y_min'
    ),
    'bone_limit_y_max': bpy.props.StringProperty(
        name='Limit Y Max', default='limit_y_max'
    ),
    'bone_limit_z_min': bpy.props.StringProperty(
        name='Limit Z Min', default='limit_z_min'
    ),
    'bone_limit_z_max': bpy.props.StringProperty(
        name='Limit Z Max', default='limit_z_max'
    ),
    # spring limit
    'bone_limit_x_spring': bpy.props.StringProperty(
        name='Limit X Spring', default='limit_x_spring'
    ),
    'bone_limit_y_spring': bpy.props.StringProperty(
        name='Limit Y Spring', default='limit_y_spring'
    ),
    'bone_limit_z_spring': bpy.props.StringProperty(
        name='Limit Z Spring', default='limit_z_spring'
    ),
    # damping limit
    'bone_limit_x_damping': bpy.props.StringProperty(
        name='Limit X Damping', default='limit_x_damping'
    ),
    'bone_limit_y_damping': bpy.props.StringProperty(
        name='Limit Y Damping', default='limit_y_damping'
    ),
    'bone_limit_z_damping': bpy.props.StringProperty(
        name='Limit Z Damping', default='limit_z_damping'
    ),
    # spring and damping
    'bone_spring': bpy.props.StringProperty(
        name='Spring', default='spring'
    ),
    'bone_damping': bpy.props.StringProperty(
        name='Damping', default='damping'
    ),
    # mass
    'bone_mass': bpy.props.StringProperty(
        name='Mass', default='mass'
    ),
    'bone_center_of_mass': bpy.props.StringProperty(
        name='Center of Mass', default='center_of_mass'
    ),
    # other
    'bone_ik_flags': bpy.props.StringProperty(
        name='IK Flags', default='ik_flags'
    ),
    'bone_breakable_force': bpy.props.StringProperty(
        name='Breakable Force', default='breakable_force'
    ),
    'bone_breakable_torque': bpy.props.StringProperty(
        name='Breakable Torque', default='breakable_torque'
    ),
    'bone_friction': bpy.props.StringProperty(
        name='Friction', default='friction'
    ),
    # action custom properties names
    'action_fps': bpy.props.StringProperty(
        name='FPS', default='fps'
    ),
    'action_speed': bpy.props.StringProperty(
        name='Speed', default='speed'
    ),
    'action_accrue': bpy.props.StringProperty(
        name='Accrue', default='accrue'
    ),
    'action_falloff': bpy.props.StringProperty(
        name='Falloff', default='falloff'
    ),
    'action_bone_part': bpy.props.StringProperty(
        name='Bone Part', default='bone_part'
    ),
    'action_flags': bpy.props.StringProperty(
        name='Flags', default='flags'
    ),
    'action_power': bpy.props.StringProperty(
        name='Power', default='power'
    )
}


class XRayPrefsCustomProperties(bpy.types.PropertyGroup):
    if not IS_28:
        for prop_name, prop_value in xray_custom_properties.items():
            exec('{0} = xray_custom_properties.get("{0}")'.format(prop_name))


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

    'category': bpy.props.EnumProperty(default='PATHS', items=category_items),
    'custom_props': bpy.props.PointerProperty(type=XRayPrefsCustomProperties)
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


@registry.requires(
    XRayPrefsCustomProperties,
    XRAY_OT_ResetPreferencesSettings
)
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

        # custom properties settings
        elif self.category == 'CUSTOM_PROPS':
            layout.row().prop(self.custom_props, 'category', expand=True)
            def draw_prop_name(name, param):
                row = layout.row()
                row.label(text=name)
                row.prop(self.custom_props, param, text='')
            # object
            if self.custom_props.category == 'OBJECT':
                draw_prop_name('Flags:', 'object_flags')
                draw_prop_name('Userdata:', 'object_userdata')
                draw_prop_name('LOD Reference:', 'object_lod_reference')
                draw_prop_name('Owner Name:', 'object_owner_name')
                draw_prop_name('Creation Time:', 'object_creation_time')
                draw_prop_name('Modif Name:', 'object_modif_name')
                draw_prop_name('Modified Time:', 'object_modified_time')
                draw_prop_name('Motion References:', 'object_motion_references')
            # mesh
            elif self.custom_props.category == 'MESH':
                draw_prop_name('Flags:', 'mesh_flags')
            # material
            elif self.custom_props.category == 'MATERIAL':
                draw_prop_name('Two Sided:', 'material_two_sided')
                draw_prop_name('Shader:', 'material_shader')
                draw_prop_name('Compile:', 'material_compile')
                draw_prop_name('Game Mtl:', 'material_game_mtl')
            # bone
            elif self.custom_props.category == 'BONE':
                layout.row().prop(self.custom_props, 'bone_category', expand=True)
                if self.custom_props.bone_category == 'MAIN':
                    draw_prop_name('Game Mtl:', 'bone_game_mtl')
                    draw_prop_name('Length:', 'bone_length')
                    # mass
                    draw_prop_name('Mass:', 'bone_mass')
                    draw_prop_name('Center of Mass:', 'bone_center_of_mass')
                    # other
                    draw_prop_name('Breakable Force:', 'bone_breakable_force')
                    draw_prop_name('Breakable Torque:', 'bone_breakable_torque')
                    draw_prop_name('Friction:', 'bone_friction')
                elif self.custom_props.bone_category == 'SHAPE':
                    draw_prop_name('Shape Flags:', 'bone_shape_flags')
                    draw_prop_name('Shape Type:', 'bone_shape_type')
                    # box shape
                    draw_prop_name('Box Shape Rotation:', 'bone_box_shape_rotation')
                    draw_prop_name('Box Shape Translate:', 'bone_box_shape_translate')
                    draw_prop_name('Box Shape Half Size:', 'bone_box_shape_half_size')
                    # sphere shape
                    draw_prop_name('Sphere Shape Position:', 'bone_sphere_shape_position')
                    draw_prop_name('Sphere Shape Radius:', 'bone_sphere_shape_radius')
                    # cylinder shape
                    draw_prop_name('Cylinder Shape Position:', 'bone_cylinder_shape_position')
                    draw_prop_name('Cylinder Shape Direction:', 'bone_cylinder_shape_direction')
                    draw_prop_name('Cylinder Shape Hight:', 'bone_cylinder_shape_hight')
                    draw_prop_name('Cylinder Shape Radius:', 'bone_cylinder_shape_radius')
                elif self.custom_props.bone_category == 'IK':
                    # ik
                    draw_prop_name('IK Joint Type:', 'bone_ik_joint_type')
                    draw_prop_name('IK Flags:', 'bone_ik_flags')
                    # limit
                    draw_prop_name('Limit X Min:', 'bone_limit_x_min')
                    draw_prop_name('Limit X Max:', 'bone_limit_x_max')
                    draw_prop_name('Limit Y Min:', 'bone_limit_y_min')
                    draw_prop_name('Limit Y Max:', 'bone_limit_y_max')
                    draw_prop_name('Limit Z Min:', 'bone_limit_z_min')
                    draw_prop_name('Limit Z Max:', 'bone_limit_z_max')
                    # spring
                    draw_prop_name('Limit X Spring:', 'bone_limit_x_spring')
                    draw_prop_name('Limit Y Spring:', 'bone_limit_y_spring')
                    draw_prop_name('Limit Z Spring:', 'bone_limit_z_spring')
                    # damping
                    draw_prop_name('Limit X Damping:', 'bone_limit_x_damping')
                    draw_prop_name('Limit Y Damping:', 'bone_limit_y_damping')
                    draw_prop_name('Limit Z Damping:', 'bone_limit_z_damping')
                    # spring and damping
                    draw_prop_name('Spring:', 'bone_spring')
                    draw_prop_name('Damping:', 'bone_damping')
            # action
            elif self.custom_props.category == 'ACTION':
                draw_prop_name('FPS:', 'action_fps')
                draw_prop_name('Speed:', 'action_speed')
                draw_prop_name('Accrue:', 'action_accrue')
                draw_prop_name('Falloff:', 'action_falloff')
                draw_prop_name('Bone Part:', 'action_bone_part')
                draw_prop_name('Flags:', 'action_flags')
                draw_prop_name('Power:', 'action_power')

        elif self.category == 'OTHERS':
            prop_bool(layout, self, 'expert_mode')
            prop_bool(layout, self, 'compact_menus')

        split = layout_split(layout, 0.6)
        split.label(text='')
        split.operator(XRAY_OT_ResetPreferencesSettings.bl_idname)


assign_props([
    (_explicit_path_op_props, _ExplicitPathOp),
    (xray_custom_properties, XRayPrefsCustomProperties)
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
