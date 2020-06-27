# pylint: disable=C0103
from os import path

import bpy

from . import registry, xray_ltx
from .ui import collapsible, xprop
from .utils import with_auto_property
from .version_utils import IS_28, assign_props
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


def PropObjectMotionsImport():
    return bpy.props.BoolProperty(
        name='Import Motions',
        description='Import embedded motions as actions',
        default=True
    )


def PropObjectMeshSplitByMaterials():
    return bpy.props.BoolProperty(
        name='Split Mesh By Materials',
        description='Import each surface (material) as separate set of faces',
        default=False
    )


def PropObjectMotionsExport():
    return bpy.props.BoolProperty(
        name='Export Motions',
        description='Export armatures actions as embedded motions',
        default=True
    )


def PropObjectTextureNamesFromPath():
    return bpy.props.BoolProperty(
        name='Texture Names From Image Paths',
        description='Generate texture names from image paths ' \
        + '(by subtract <gamedata/textures> prefix and <file-extension> suffix)',
        default=True
    )


def PropObjectBonesCustomShapes():
    return bpy.props.BoolProperty(
        name='Custom Shapes For Bones',
        description='Use custom shapes for imported bones',
        default=True
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


def prop_details_models_in_a_row():
    return bpy.props.BoolProperty(name='Details Models in a Row', default=True)


def prop_details_load_slots():
    return bpy.props.BoolProperty(name='Load Slots', default=True)


def prop_details_format():
    return bpy.props.EnumProperty(
        name='Details Format',
        items=(
            ('builds_1096-1230', 'Builds 1096-1230', ''),
            ('builds_1233-1558', 'Builds 1233-1558', '')
        )
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
def _auto_path(obj, self_name, path_suffix, checker):
    if obj.fs_ltx_file:
        if not path.exists(obj.fs_ltx_file):
            return ''
        try:
            fs = xray_ltx.StalkerLtxParser(obj.fs_ltx_file)
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
        value = getattr(obj, prop)
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
class _ExplicitPathOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.explicit_path'
    bl_label = 'Make Explicit'
    bl_description = 'Make this path explicit using the automatically calculated value'

    if not IS_28:
        for prop_name, prop_value in _explicit_path_op_props.items():
            exec('{0} = _explicit_path_op_props.get("{0}")'.format(prop_name))

    def execute(self, _context):
        prefs = get_preferences()
        value = getattr(prefs, with_auto_property.build_auto_id(self.path))
        setattr(prefs, self.path, value)
        return {'FINISHED'}


def update_paths(self, context):
    self.gamedata_folder = ''
    self.textures_folder = ''
    self.gamemtl_file = ''
    self.eshader_file = ''
    self.cshader_file = ''
    self.objects_folder = ''


plugin_preferences_props = {
    'expert_mode': bpy.props.BoolProperty(
        name='Expert Mode', description='Show additional properties/controls'
    ),
    'compact_menus': bpy.props.BoolProperty(
        name='Compact Import/Export Menus', update=update_menu_func
    ),
    'sdk_version': PropSDKVersion(),
    'object_motions_import': PropObjectMotionsImport(),
    'object_motions_export': PropObjectMotionsExport(),
    'object_mesh_split_by_mat': PropObjectMeshSplitByMaterials(),
    'object_texture_names_from_path': PropObjectTextureNamesFromPath(),
    'object_bones_custom_shapes': PropObjectBonesCustomShapes(),
    'anm_create_camera': PropAnmCameraAnimation(),
    'fs_ltx_file': bpy.props.StringProperty(
        subtype='FILE_PATH', update=update_paths, name='fs.ltx File'
    ),
    'details_models_in_a_row': prop_details_models_in_a_row(),
    'load_slots': prop_details_load_slots(),
    'details_format': prop_details_format()
}


@registry.module_thing
@with_auto_property(
    bpy.props.StringProperty, 'gamedata_folder',
    lambda self: _auto_path(self, 'gamedata_folder', '', path.isdir),
    name='Gamedata Folder',
    description='Path to the \'gamedata\' directory',
    subtype='DIR_PATH',
    overrides={'subtype': 'NONE'},
)
@with_auto_property(
    bpy.props.StringProperty, 'textures_folder',
    lambda self: _auto_path(self, 'textures_folder', 'textures', path.isdir),
    name='Textures Folder',
    description='Path to the \'gamedata/textures\' directory',
    subtype='DIR_PATH',
    overrides={'subtype': 'NONE'},
)
@with_auto_property(
    bpy.props.StringProperty, 'gamemtl_file',
    lambda self: _auto_path(self, 'gamemtl_file', 'gamemtl.xr', path.isfile),
    name='GameMtl File',
    description='Path to the \'gamemtl.xr\' file',
    subtype='FILE_PATH',
    overrides={'subtype': 'NONE'},
)
@with_auto_property(
    bpy.props.StringProperty, 'eshader_file',
    lambda self: _auto_path(self, 'eshader_file', 'shaders.xr', path.isfile),
    name='EShader File',
    description='Path to the \'shaders.xr\' file',
    subtype='FILE_PATH',
    overrides={'subtype': 'NONE'},
)
@with_auto_property(
    bpy.props.StringProperty, 'cshader_file',
    lambda self: _auto_path(self, 'cshader_file', 'shaders_xrlc.xr', path.isfile),
    name='CShader File',
    description='Path to the \'shaders_xrlc.xr\' file',
    subtype='FILE_PATH',
    overrides={'subtype': 'NONE'},
)
@with_auto_property(
    bpy.props.StringProperty, 'objects_folder',
    lambda self: _auto_path(self, 'objects_folder', path.join('..', 'rawdata', 'objects'), path.isdir),
    name='Objects Folder',
    description='Path to the \'rawdata/objects\' directory',
    subtype='DIR_PATH',
    overrides={'subtype': 'NONE'},
)
class PluginPreferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    if not IS_28:
        for prop_name, prop_value in plugin_preferences_props.items():
            exec('{0} = plugin_preferences_props.get("{0}")'.format(prop_name))

    def draw(self, _context):
        def prop_bool(layout, data, prop):
            # row = layout.row()
            # row.label(text=getattr(self.__class__, prop)[1]['name'] + ':')
            # row.prop(data, prop, text='')
            layout.prop(data, prop)

        def prop_auto(layout, data, prop):
            eprop = prop
            if not getattr(data, prop):
                nprop = with_auto_property.build_auto_id(prop)
                if getattr(data, nprop):
                    eprop = nprop
            if eprop == prop:
                layout.prop(data, eprop)
            else:
                _, lay = xprop(layout, data, eprop, enabled=False)
                operator = lay.operator(_ExplicitPathOp.bl_idname, icon='MODIFIER', text='')
                operator.path = prop

        layout = self.layout

        row = layout.row(align=True)
        row.menu(PREFS_MT_xray_presets.__name__, text=PREFS_MT_xray_presets.bl_label)
        row.operator(AddPresetXrayPrefs.bl_idname, text='', icon='ADD')
        row.operator(AddPresetXrayPrefs.bl_idname, text='', icon='REMOVE').remove_active = True

        layout.prop(self, 'fs_ltx_file')

        prop_auto(layout, self, 'gamedata_folder')
        prop_auto(layout, self, 'textures_folder')
        prop_auto(layout, self, 'gamemtl_file')
        prop_auto(layout, self, 'eshader_file')
        prop_auto(layout, self, 'cshader_file')
        prop_auto(layout, self, 'objects_folder')

        _, box = collapsible.draw(layout, 'plugin_prefs:defaults', 'Defaults', style='tree')
        if box:
            row = box.row()
            row.label(text='SDK Version:')
            row.prop(self, 'sdk_version', expand=True)

            _, box_n = collapsible.draw(box, 'plugin_prefs:defaults.object', 'Object', style='tree')
            if box_n:
                prop_bool(box_n, self, 'object_motions_import')
                prop_bool(box_n, self, 'object_motions_export')
                prop_bool(box_n, self, 'object_texture_names_from_path')
                prop_bool(box_n, self, 'object_mesh_split_by_mat')
                prop_bool(box_n, self, 'object_bones_custom_shapes')

            _, box_n = collapsible.draw(box, 'plugin_prefs:defaults.anm', 'Animation', style='tree')
            if box_n:
                prop_bool(box_n, self, 'anm_create_camera')

            _, box_n = collapsible.draw(box, 'plugin_prefs:defaults.details', 'Details', style='tree')
            if box_n:
                prop_bool(box_n, self, 'details_models_in_a_row')
                prop_bool(box_n, self, 'load_slots')
                box_n.label(text='Format:')
                row = box_n.row()
                row.prop(self, 'details_format', expand=True)

        prop_bool(layout, self, 'expert_mode')
        prop_bool(layout, self, 'compact_menus')


assign_props([
    (_explicit_path_op_props, _ExplicitPathOp),
])
assign_props([
    (plugin_preferences_props, PluginPreferences),
], replace=False)


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
    preset_values = [
        'prefs.gamedata_folder',
        'prefs.textures_folder',
        'prefs.gamemtl_file',
        'prefs.eshader_file',
        'prefs.cshader_file',
        'prefs.objects_folder',
        'prefs.sdk_version',
        'prefs.object_motions_import',
        'prefs.object_motions_export',
        'prefs.object_texture_names_from_path',
        'prefs.object_mesh_split_by_mat',
        'prefs.object_bones_custom_shapes',
        'prefs.anm_create_camera',
        'prefs.expert_mode',
        'prefs.compact_menus'
    ]
    preset_subdir = 'io_scene_xray/preferences'
