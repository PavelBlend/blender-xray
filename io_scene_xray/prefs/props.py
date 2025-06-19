# standart modules
import os
import sys
import traceback

# blender modules
import bpy

# addon modules
from . import hotkeys
from .. import rw
from .. import log
from .. import menus
from .. import formats
from .. import utils
from .. import text


def _norm_path(path):
    if path and path[-1] == os.sep:
        path = path[ : -1]
    return path


def _search_folder(pref, prop_names):
    for prop_name in prop_names:
        prop_value = getattr(pref, prop_name)
        if prop_value:
            prop_value = _norm_path(prop_value)
            dirname = os.path.dirname(prop_value)
            if dirname == prop_value:
                continue    # os.path.dirname('T:') == 'T:'
            return dirname


def _get_game_raw_folders(pref):
    game_folder = _norm_path(pref.gamedata_folder)
    raw_folder = _norm_path(pref.rawdata_folder)

    if not game_folder:
        prop_names = (
            'textures_folder',
            'meshes_folder',
            'levels_folder',
            'gamemtl_file',
            'eshader_file',
            'cshader_file'
        )
        game_folder = _search_folder(pref, prop_names)

    if not raw_folder:
        prop_names = (
            'objects_folder',
            'maps_folder',
            'groups_folder'
        )
        raw_folder = _search_folder(pref, prop_names)

    if game_folder and not raw_folder:
        suffix = path_props_suffix_values['rawdata_folder']
        raw_folder = os.path.join(
            os.path.dirname(game_folder),
            suffix
        )

    elif not game_folder and raw_folder:
        suffix = path_props_suffix_values['gamedata_folder']
        game_folder = os.path.join(
            os.path.dirname(raw_folder),
            suffix
        )

    return game_folder, raw_folder


def update_menu_func(self, context):
    menus.append_menu_func()


def update_paths(pref, context):
    if not pref.use_update:
        return

    not_found_paths = set()

    game_folder, raw_folder = _get_game_raw_folders(pref)

    for prop in path_props_suffix_values.keys():

        prop_val = getattr(pref, prop)
        if prop_val:
            setattr(pref, build_auto_id(prop), prop_val)
            continue

        value, not_found = _auto_path(pref, prop, game_folder, raw_folder)

        if not_found:
            not_found_paths.add(os.path.abspath(not_found))

        prop_type = path_props_types[prop]
        if value and prop_type == DIRECTORY:
            if not value.endswith(os.sep):
                value += os.sep

        setattr(pref, build_auto_id(prop), value)

    if not_found_paths:
        not_found_paths = list(not_found_paths)
        not_found_paths.sort()
        utils.draw.show_message(
            text.get_tip(text.error.file_folder_not_found),
            not_found_paths,
            text.get_tip(text.error.error_title),
            'ERROR'
        )


class XRayKeyMap(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    operator = bpy.props.StringProperty()


class PathsSettings(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    sdk_ver = formats.ie.prop_sdk_ver()

    # path props
    fs_ltx_file = bpy.props.StringProperty(
        subtype='FILE_PATH',
        name='fs.ltx File',
        update=update_paths
    )

    # gamedata folders
    gamedata_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    )
    textures_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    )
    meshes_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    )
    levels_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    )

    # gamedata files
    gamemtl_file = bpy.props.StringProperty(
        subtype='FILE_PATH',
        update=update_paths
    )
    eshader_file = bpy.props.StringProperty(
        subtype='FILE_PATH',
        update=update_paths
    )
    cshader_file = bpy.props.StringProperty(
        subtype='FILE_PATH',
        update=update_paths
    )

    # rawdata folders
    rawdata_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    )
    objects_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    )
    maps_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    )
    groups_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    )

    # path auto props
    gamedata_folder_auto = bpy.props.StringProperty()
    textures_folder_auto = bpy.props.StringProperty()
    meshes_folder_auto = bpy.props.StringProperty()
    levels_folder_auto = bpy.props.StringProperty()

    gamemtl_file_auto = bpy.props.StringProperty()
    eshader_file_auto = bpy.props.StringProperty()
    cshader_file_auto = bpy.props.StringProperty()

    rawdata_folder_auto = bpy.props.StringProperty()
    objects_folder_auto = bpy.props.StringProperty()
    maps_folder_auto = bpy.props.StringProperty()
    groups_folder_auto = bpy.props.StringProperty()

    use_update = bpy.props.BoolProperty(default=True)


class PathsConfigs(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    platform = bpy.props.StringProperty()
    mod = bpy.props.StringProperty()


def _get_enable_prop():
    return bpy.props.BoolProperty(default=True, update=update_menu_func)


prefs_props = {
    # path props
    'fs_ltx_file': bpy.props.StringProperty(
        subtype='FILE_PATH',
        name='fs.ltx File',
        update=update_paths
    ),
    'gamedata_folder': bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    ),
    'textures_folder': bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    ),
    'meshes_folder': bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    ),
    'levels_folder': bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    ),
    'gamemtl_file': bpy.props.StringProperty(
        subtype='FILE_PATH',
        update=update_paths
    ),
    'eshader_file': bpy.props.StringProperty(
        subtype='FILE_PATH',
        update=update_paths
    ),
    'cshader_file': bpy.props.StringProperty(
        subtype='FILE_PATH',
        update=update_paths
    ),
    'rawdata_folder': bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    ),
    'objects_folder': bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    ),
    'maps_folder': bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    ),
    'groups_folder': bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=update_paths
    ),

    # path auto props

    'gamedata_folder_auto': bpy.props.StringProperty(),
    'textures_folder_auto': bpy.props.StringProperty(),
    'meshes_folder_auto': bpy.props.StringProperty(),
    'levels_folder_auto': bpy.props.StringProperty(),

    'gamemtl_file_auto': bpy.props.StringProperty(),
    'eshader_file_auto': bpy.props.StringProperty(),
    'cshader_file_auto': bpy.props.StringProperty(),

    'rawdata_folder_auto': bpy.props.StringProperty(),
    'objects_folder_auto': bpy.props.StringProperty(),
    'maps_folder_auto': bpy.props.StringProperty(),
    'groups_folder_auto': bpy.props.StringProperty(),

    # path advanced props
    'paths_presets': bpy.props.CollectionProperty(type=PathsSettings),
    'paths_presets_index': bpy.props.IntProperty(),

    'paths_configs': bpy.props.CollectionProperty(type=PathsConfigs),
    'paths_configs_index': bpy.props.IntProperty(),

    'used_config': bpy.props.StringProperty(),

    # others
    'compact_menus': bpy.props.BoolProperty(
        name='Compact Import/Export Menus',
        update=update_menu_func
    ),
    'check_updates': bpy.props.BoolProperty(
        default=True,
        name='Check for Updates after Starting Blender'
    ),
    'use_batch_status': bpy.props.BoolProperty(
        default=False,
        name='Print Batch Import/Export Status to the Console'
    ),

    'paths_mode': bpy.props.EnumProperty(
        default='BASE',
        items=(('BASE', 'Base', ''), ('ADVANCED', 'Advanced', ''))
    ),

    # defaults
    'defaults_category': bpy.props.EnumProperty(
        default='OBJECT',
        items=(
            ('OBJECT', ' Object ', ''),
            ('SKLS', 'Skls', ''),
            ('OGF', 'Ogf', ''),
            ('OMF', 'Omf', ''),
            ('ANM', 'Anm', ''),
            ('BONES', ' Bones ', ''),
            ('DM', 'Dm', ''),
            ('DETAILS', 'Details', ''),
            ('SCENE', ' Scene ', ''),
            ('PART', 'Part', ''),
            ('GROUP', 'Group', '')
        )
    ),

    # object import props
    'sdk_version': formats.ie.prop_sdk_ver(),
    'object_motions_import': formats.ie.prop_imp_motions(),
    'object_mesh_split_by_mat': formats.ie.prop_split_by_mats(),

    # object export props
    'export_object_sdk_version': formats.ie.prop_sdk_ver(),
    'smoothing_out_of': formats.ie.prop_smooth(),
    'object_motions_export': formats.ie.prop_exp_motions(),
    'object_texture_names_from_path': formats.ie.prop_tex_from_path(),
    'export_object_use_export_paths': formats.ie.prop_exp_paths(),

    # anm import props
    'anm_create_camera': formats.ie.prop_camera_anim(),

    # anm export props
    'anm_format_version': formats.ie.prop_anm_ver(),

    # skl/skls import props
    'add_to_motion_list': formats.ie.prop_add_acts_to_list(),

    # skl/skls export props
    'skl_export_fmt_ver': formats.ie.prop_sdk_ver(),

    # bones import props
    'bones_import_bone_parts': formats.ie.prop_imp_bone_parts(),
    'bones_import_bone_properties': formats.ie.prop_imp_bone_props(),

    # bones export props
    'bones_export_bone_parts': formats.ie.prop_exp_bone_parts(),
    'bones_export_bone_properties': formats.ie.prop_exp_bone_props(),

    # details import props
    'details_models_in_a_row': formats.ie.prop_models_in_row(),
    'load_slots': formats.ie.prop_load_slots(),
    'details_format': formats.ie.prop_details_fmt(),

    # details export props
    'details_texture_names_from_path': formats.ie.prop_tex_from_path(),
    'format_version': formats.ie.prop_details_ver(),

    # dm export props
    'dm_texture_names_from_path': formats.ie.prop_tex_from_path(),

    # ogf import props
    'ogf_import_motions': formats.ie.prop_imp_motions(),

    # ogf export props
    'ogf_texture_names_from_path': formats.ie.prop_tex_from_path(),
    'ogf_export_motions': formats.ie.prop_exp_motions(),
    'ogf_export_fmt_ver': formats.ie.prop_sdk_ver(),
    'ogf_export_hq_motions': formats.ie.prop_high_qual(),
    'ogf_export_use_export_paths': formats.ie.prop_exp_paths(),

    # omf import props
    'omf_import_motions': formats.ie.prop_imp_motions(),
    'import_bone_parts': formats.ie.prop_imp_bone_parts(),
    'omf_add_actions_to_motion_list': formats.ie.prop_add_acts_to_list(),

    # omf export props
    'omf_export_fmt_ver': formats.ie.prop_sdk_ver(),
    'omf_export_bone_parts': formats.ie.prop_exp_bone_parts(),
    'omf_export_mode': formats.ie.prop_exp_mode(),
    'omf_motions_export': formats.ie.prop_exp_motions(),
    'omf_high_quality': formats.ie.prop_high_qual(),

    # scene selection import props
    'scene_selection_sdk_version': formats.ie.prop_sdk_ver(),
    'scene_selection_mesh_split_by_mat': formats.ie.prop_split_by_mats(),

    # part import props
    'part_sdk_version': formats.ie.prop_sdk_ver(),
    'part_mesh_split_by_mat': formats.ie.prop_split_by_mats(),

    # part export props
    'part_exp_sdk_ver': formats.ie.prop_sdk_ver(),

    # group import props
    'group_sdk_ver': formats.ie.prop_sdk_ver(),
    'group_split_by_mat': formats.ie.prop_split_by_mats(),

    # keymap
    'keymaps_collection': bpy.props.CollectionProperty(type=XRayKeyMap),
    'keymaps_collection_index': bpy.props.IntProperty(options={'SKIP_SAVE'}),

    # enable import plugins
    'enable_object_import': _get_enable_prop(),
    'enable_anm_import': _get_enable_prop(),
    'enable_dm_import': _get_enable_prop(),
    'enable_details_import': _get_enable_prop(),
    'enable_skls_import': _get_enable_prop(),
    'enable_bones_import': _get_enable_prop(),
    'enable_err_import': _get_enable_prop(),
    'enable_scene_import': _get_enable_prop(),
    'enable_level_import': _get_enable_prop(),
    'enable_omf_import': _get_enable_prop(),
    'enable_ogf_import': _get_enable_prop(),
    'enable_part_import': _get_enable_prop(),
    'enable_group_import': _get_enable_prop(),

    # enable export plugins
    'enable_object_export': _get_enable_prop(),
    'enable_anm_export': _get_enable_prop(),
    'enable_dm_export': _get_enable_prop(),
    'enable_details_export': _get_enable_prop(),
    'enable_skls_export': _get_enable_prop(),
    'enable_skl_export': _get_enable_prop(),
    'enable_bones_export': _get_enable_prop(),
    'enable_scene_export': _get_enable_prop(),
    'enable_level_export': _get_enable_prop(),
    'enable_omf_export': _get_enable_prop(),
    'enable_ogf_export': _get_enable_prop(),
    'enable_part_export': _get_enable_prop(),
    'enable_group_export': _get_enable_prop(),

    'category': bpy.props.EnumProperty(
        default='PATHS',
        items=(
            ('PATHS', 'Paths', ''),
            ('DEFAULTS', 'Defaults', ''),
            ('PLUGINS', 'Formats', ''),
            ('KEYMAP', 'Keymap', ''),
            ('CUSTOM_PROPS', 'Custom Props', ''),
            ('OTHERS', 'Others', '')
        )
    ),

    'custom_owner_name': bpy.props.StringProperty(),

    # viewport props
    'gl_shape_color': bpy.props.FloatVectorProperty(
        name='Unselected Shape',
        default=(0.0, 0.0, 1.0, 0.5),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    ),
    'gl_active_shape_color': bpy.props.FloatVectorProperty(
        name='Active Shape',
        default=(1.0, 1.0, 1.0, 0.7),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    ),
    'gl_select_shape_color': bpy.props.FloatVectorProperty(
        name='Selected Shape',
        default=(0.0, 1.0, 1.0, 0.7),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    ),
    'gl_object_mode_shape_color': bpy.props.FloatVectorProperty(
        name='Shape in Object Mode',
        default=(0.8, 0.8, 0.8, 0.8),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    ),
    'gl_solid_col_desel': bpy.props.FloatVectorProperty(
        name='Unselected Shape',
        default=(0.0, 0.0, 1.0, 0.1),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    ),
    'gl_solid_col_active': bpy.props.FloatVectorProperty(
        name='Active Shape',
        default=(1.0, 1.0, 1.0, 0.15),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    ),
    'gl_solid_col_sel': bpy.props.FloatVectorProperty(
        name='Selected Shape',
        default=(0.0, 1.0, 1.0, 0.15),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    ),
    'gl_solid_col_obj': bpy.props.FloatVectorProperty(
        name='Shape in Object Mode',
        default=(0.8, 0.8, 0.8, 0.15),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    ),

    # custom data props
    'object_split_normals': bpy.props.BoolProperty(
        name='Use *.object Split Normals',
        default=False
    )
}

custom_props = {
    # main
    'category': bpy.props.EnumProperty(
        name='Custom Property Category',
        default='OBJECT',
        items=(
            ('OBJECT', 'Object', ''),
            ('MESH', 'Mesh', ''),
            ('MATERIAL', 'Material', ''),
            ('BONE', 'Bone', ''),
            ('ACTION', 'Action', '')
        )
    ),
    'bone_category': bpy.props.EnumProperty(
        name='Custom Property Bone Category',
        default='MAIN',
        items=(
            ('MAIN', 'Main', ''),
            ('SHAPE', 'Shape', ''),
            ('IK', 'IK', '')
        )
    ),

    # object
    'object_flags': bpy.props.StringProperty(
        name='Flags',
        default='flags'
    ),
    'object_userdata': bpy.props.StringProperty(
        name='Userdata',
        default='userdata'
    ),
    'object_lod_reference': bpy.props.StringProperty(
        name='LOD Reference',
        default='lod_reference'
    ),
    'object_owner_name': bpy.props.StringProperty(
        name='Owner Name',
        default='owner_name'
    ),
    'object_creation_time': bpy.props.StringProperty(
        name='Creation Time',
        default='creation_time'
    ),
    'object_modif_name': bpy.props.StringProperty(
        name='Modif Name',
        default='modif_name'
    ),
    'object_modified_time': bpy.props.StringProperty(
        name='Modified Time',
        default='modified_time'
    ),
    'object_motion_references': bpy.props.StringProperty(
        name='Motion References',
        default='motion_references'
    ),

    # mesh
    'mesh_flags': bpy.props.StringProperty(
        name='Flags',
        default='flags'
    ),

    # material
    'material_two_sided': bpy.props.StringProperty(
        name='Two Sided',
        default='two_sided'
    ),
    'material_shader': bpy.props.StringProperty(
        name='Shader',
        default='shader'
    ),
    'material_compile': bpy.props.StringProperty(
        name='Compile',
        default='compile'
    ),
    'material_game_mtl': bpy.props.StringProperty(
        name='Game Mtl',
        default='game_mtl'
    ),

    # bone
    'bone_game_mtl': bpy.props.StringProperty(
        name='Game Mtl',
        default='game_mtl'
    ),
    'bone_length': bpy.props.StringProperty(
        name='Length',
        default='length'
    ),
    'bone_shape_flags': bpy.props.StringProperty(
        name='Shape Flags',
        default='shape_flags'
    ),
    'bone_shape_type': bpy.props.StringProperty(
        name='Shape Type',
        default='shape_type'
    ),
    'bone_part': bpy.props.StringProperty(
        name='Bone Part',
        default='bone_part'
    ),

    # box shape
    'bone_box_shape_rotation': bpy.props.StringProperty(
        name='Box Shape Rotation',
        default='box_shape_rotation'
    ),
    'bone_box_shape_translate': bpy.props.StringProperty(
        name='Box Shape Translate',
        default='box_shape_translate'
    ),
    'bone_box_shape_half_size': bpy.props.StringProperty(
        name='Box Shape Half Size',
        default='box_shape_half_size'
    ),

    # sphere shape
    'bone_sphere_shape_position': bpy.props.StringProperty(
        name='Sphere Shape Position',
        default='sphere_shape_position'
    ),
    'bone_sphere_shape_radius': bpy.props.StringProperty(
        name='Sphere Shape Radius',
        default='sphere_shape_radius'
    ),

    # cylinder shape
    'bone_cylinder_shape_position': bpy.props.StringProperty(
        name='Cylinder Shape Position',
        default='cylinder_shape_position'
    ),
    'bone_cylinder_shape_direction': bpy.props.StringProperty(
        name='Cylinder Shape Direction',
        default='cylinder_shape_direction'
    ),
    'bone_cylinder_shape_hight': bpy.props.StringProperty(
        name='Cylinder Shape Hight',
        default='cylinder_shape_hight'
    ),
    'bone_cylinder_shape_radius': bpy.props.StringProperty(
        name='Cylinder Shape Radius',
        default='cylinder_shape_radius'
    ),

    # ik joint type
    'bone_ik_joint_type': bpy.props.StringProperty(
        name='IK Joint Type',
        default='ik_joint_type'
    ),

    # limit
    'bone_limit_x_min': bpy.props.StringProperty(
        name='Limit X Min',
        default='limit_x_min'
    ),
    'bone_limit_x_max': bpy.props.StringProperty(
        name='Limit X Max',
        default='limit_x_max'
    ),
    'bone_limit_y_min': bpy.props.StringProperty(
        name='Limit Y Min',
        default='limit_y_min'
    ),
    'bone_limit_y_max': bpy.props.StringProperty(
        name='Limit Y Max',
        default='limit_y_max'
    ),
    'bone_limit_z_min': bpy.props.StringProperty(
        name='Limit Z Min',
        default='limit_z_min'
    ),
    'bone_limit_z_max': bpy.props.StringProperty(
        name='Limit Z Max',
        default='limit_z_max'
    ),

    # spring limit
    'bone_limit_x_spring': bpy.props.StringProperty(
        name='Limit X Spring',
        default='limit_x_spring'
    ),
    'bone_limit_y_spring': bpy.props.StringProperty(
        name='Limit Y Spring',
        default='limit_y_spring'
    ),
    'bone_limit_z_spring': bpy.props.StringProperty(
        name='Limit Z Spring',
        default='limit_z_spring'
    ),

    # damping limit
    'bone_limit_x_damping': bpy.props.StringProperty(
        name='Limit X Damping',
        default='limit_x_damping'
    ),
    'bone_limit_y_damping': bpy.props.StringProperty(
        name='Limit Y Damping',
        default='limit_y_damping'
    ),
    'bone_limit_z_damping': bpy.props.StringProperty(
        name='Limit Z Damping',
        default='limit_z_damping'
    ),

    # spring and damping
    'bone_spring': bpy.props.StringProperty(
        name='Spring',
        default='spring'
    ),
    'bone_damping': bpy.props.StringProperty(
        name='Damping',
        default='damping'
    ),

    # mass
    'bone_mass': bpy.props.StringProperty(
        name='Mass',
        default='mass'
    ),
    'bone_center_of_mass': bpy.props.StringProperty(
        name='Center of Mass',
        default='center_of_mass'
    ),

    # other
    'bone_ik_flags': bpy.props.StringProperty(
        name='IK Flags',
        default='ik_flags'
    ),
    'bone_breakable_force': bpy.props.StringProperty(
        name='Breakable Force',
        default='breakable_force'
    ),
    'bone_breakable_torque': bpy.props.StringProperty(
        name='Breakable Torque',
        default='breakable_torque'
    ),
    'bone_friction': bpy.props.StringProperty(
        name='Friction',
        default='friction'
    ),

    # action
    'action_fps': bpy.props.StringProperty(
        name='FPS',
        default='fps'
    ),
    'action_speed': bpy.props.StringProperty(
        name='Speed',
        default='speed'
    ),
    'action_accrue': bpy.props.StringProperty(
        name='Accrue',
        default='accrue'
    ),
    'action_falloff': bpy.props.StringProperty(
        name='Falloff', 
        default='falloff'
    ),
    'action_bone_part': bpy.props.StringProperty(
        name='Bone Part',
        default='bone_part'
    ),
    'action_flags': bpy.props.StringProperty(
        name='Flags',
        default='flags'
    ),
    'action_power': bpy.props.StringProperty(
        name='Power',
        default='power'
    )
}


def build_auto_id(prop):
    return prop + '_auto'


__AUTO_PROPS__ = [

    'gamedata_folder',
    'textures_folder',
    'meshes_folder',
    'levels_folder',

    'gamemtl_file',
    'eshader_file',
    'cshader_file',

    'rawdata_folder',
    'objects_folder',
    'maps_folder',
    'groups_folder'

]

fs_props = {

    'gamedata_folder': ('$game_data$', None),
    'textures_folder': ('$game_textures$', None),
    'meshes_folder': ('$game_meshes$', None),
    'levels_folder': ('$game_levels$', None),

    'gamemtl_file': ('$game_data$', 'gamemtl.xr'),
    'eshader_file': ('$game_data$', 'shaders.xr'),
    'cshader_file': ('$game_data$', 'shaders_xrlc.xr'),

    'rawdata_folder': ('$sdk_root_raw$', None),
    'objects_folder': ('$objects$', None),
    'maps_folder': ('$maps$', None),
    'groups_folder': ('$groups$', None)

}


def _clear_paths():
    pref = utils.version.get_preferences()
    pref.use_update = False

    for prop in path_props_suffix_values.keys():
        setattr(pref, build_auto_id(prop), '')
        setattr(pref, prop, '')

    pref.use_update = True


def _auto_path_fs_ltx(prefs, prop_name):
    if not os.path.exists(prefs.fs_ltx_file):
        return '', prefs.fs_ltx_file

    try:
        fs = rw.ltx.LtxParser()
        fs.from_file(prefs.fs_ltx_file)

    except log.AppError:
        traceback.print_exc()
        utils.draw.show_message(
            text.get_tip(text.error.ltx_invalid_syntax),
            (prefs.fs_ltx_file, sys.exc_info()[1]),
            text.get_tip(text.error.error_title),
            'ERROR'
        )
        _clear_paths()
        raise BaseException('error')

    except BaseException:
        _clear_paths()
        raise BaseException('error')

    prop_key, file_name = fs_props[prop_name]
    dir_path = fs.values.get(prop_key, None)

    if dir_path is None:
        utils.draw.show_message(
            text.get_tip(text.error.ltx_no_param),
            (prop_key, ),
            text.get_tip(text.error.error_title),
            'ERROR'
        )
        _clear_paths()
        raise BaseException('error')

    if file_name:
        result = os.path.join(dir_path, file_name)
    else:
        result = dir_path

    return result, None


def _auto_path_prop(prefs, prop_name, game_folder, raw_folder):
    result = ''
    parent = path_parents[prop_name]
    suffix = path_props_suffix_values[prop_name]

    if parent == 'gamedata_folder' and game_folder:
        result = os.path.join(game_folder, suffix)

    elif parent == 'rawdata_folder' and raw_folder:
        result = os.path.join(raw_folder, suffix)

    else:
        if prop_name == 'gamedata_folder':
            if game_folder:
                result = game_folder
            elif raw_folder:
                dirname = os.path.dirname(raw_folder)
                result = os.path.join(dirname, suffix)
        elif prop_name == 'rawdata_folder':
            if raw_folder:
                result = raw_folder
            elif game_folder:
                dirname = os.path.dirname(game_folder)
                result = os.path.join(dirname, suffix)

    prop_type = path_props_types[prop_name]

    if prop_type == DIRECTORY:
        checker = os.path.isdir
    elif prop_type == FILE:
        checker = os.path.isfile

    if checker(result):
        return result, None

    return '', result


def _auto_path(prefs, prop_name, game_folder, raw_folder):
    if prefs.fs_ltx_file:
        return _auto_path_fs_ltx(prefs, prop_name)
    else:
        return _auto_path_prop(prefs, prop_name, game_folder, raw_folder)


path_props_suffix_values = {

    'gamedata_folder': 'gamedata',
    'textures_folder': 'textures',
    'meshes_folder': 'meshes',
    'levels_folder': 'levels',

    'gamemtl_file': 'gamemtl.xr',
    'eshader_file': 'shaders.xr',
    'cshader_file': 'shaders_xrlc.xr',

    'rawdata_folder': 'rawdata',
    'objects_folder': 'objects',
    'maps_folder': 'maps',
    'groups_folder': 'groups'

}

path_parents = {

    'gamedata_folder': None,
    'textures_folder': 'gamedata_folder',
    'meshes_folder': 'gamedata_folder',
    'levels_folder': 'gamedata_folder',

    'gamemtl_file': 'gamedata_folder',
    'eshader_file': 'gamedata_folder',
    'cshader_file': 'gamedata_folder',

    'rawdata_folder': None,
    'objects_folder': 'rawdata_folder',
    'maps_folder': 'rawdata_folder',
    'groups_folder': 'rawdata_folder'

}

FILE = 'FILE'
DIRECTORY = 'DIRECTORY'

path_props_types = {

    'gamedata_folder': DIRECTORY,
    'textures_folder': DIRECTORY,
    'meshes_folder': DIRECTORY,
    'levels_folder': DIRECTORY,

    'gamemtl_file': FILE,
    'eshader_file': FILE,
    'cshader_file': FILE,

    'rawdata_folder': DIRECTORY,
    'objects_folder': DIRECTORY,
    'maps_folder': DIRECTORY,
    'groups_folder': DIRECTORY

}


class XRayPrefsCustomProperties(bpy.types.PropertyGroup):
    for prop_name in custom_props.keys():
        exec('{0} = custom_props.get("{0}")'.format(prop_name))


class XRAY_OT_add_keymap(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.add_keymap'
    bl_label = 'Add Keymap'

    operator = bpy.props.StringProperty()

    def execute(self, context):
        hotkeys.add_keymaps(only=self.operator)
        return {'FINISHED'}


classes = (
    XRayKeyMap,
    PathsSettings,
    PathsConfigs,
    XRAY_OT_add_keymap,
    XRayPrefsCustomProperties
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
