# standart modules
import os
import sys
import traceback

# blender modules
import bpy

# addon modules
from . import hotkeys
from .. import rw
from .. import utils
from .. import text


plugin_preferences_props = (
    'fs_ltx_file',
    'gamedata_folder',
    'textures_folder',
    'meshes_folder',
    'levels_folder',
    'gamemtl_file',
    'eshader_file',
    'cshader_file',
    'objects_folder',

    'gamedata_folder_auto',
    'textures_folder_auto',
    'meshes_folder_auto',
    'levels_folder_auto',
    'gamemtl_file_auto',
    'eshader_file_auto',
    'cshader_file_auto',
    'objects_folder_auto',

    'compact_menus',
    'paths_mode',
    'defaults_category',
    'sdk_version',
    'object_motions_import',
    'object_mesh_split_by_mat',
    'export_object_sdk_version',
    'smoothing_out_of',
    'object_motions_export',
    'object_texture_names_from_path',
    'export_object_use_export_paths',
    'anm_create_camera',
    'anm_format_version',
    'add_to_motion_list',
    'bones_import_bone_parts',
    'bones_import_bone_properties',
    'bones_export_bone_parts',
    'bones_export_bone_properties',
    'details_models_in_a_row',
    'load_slots',
    'details_format',
    'details_texture_names_from_path',
    'format_version',
    'dm_texture_names_from_path',
    'ogf_import_motions',
    'ogf_texture_names_from_path',
    'ogf_export_motions',
    'ogf_export_fmt_ver',
    'ogf_export_hq_motions',
    'ogf_export_use_export_paths',
    'omf_import_motions',
    'import_bone_parts',
    'omf_add_actions_to_motion_list',
    'omf_export_bone_parts',
    'omf_export_mode',
    'omf_motions_export',
    'omf_high_quality',
    'scene_selection_sdk_version',
    'scene_selection_mesh_split_by_mat',
    'part_sdk_version',
    'part_mesh_split_by_mat',
    'keymaps_collection',
    'keymaps_collection_index',
    'enable_object_import',
    'enable_anm_import',
    'enable_dm_import',
    'enable_details_import',
    'enable_skls_import',
    'enable_bones_import',
    'enable_err_import',
    'enable_scene_import',
    'enable_level_import',
    'enable_omf_import',
    'enable_ogf_import',
    'enable_part_import',
    'enable_object_export',
    'enable_anm_export',
    'enable_dm_export',
    'enable_details_export',
    'enable_skls_export',
    'enable_skl_export',
    'enable_bones_export',
    'enable_scene_export',
    'enable_level_export',
    'enable_omf_export',
    'enable_ogf_export',
    'category',
    'custom_owner_name',
    'gl_shape_color',
    'gl_active_shape_color',
    'gl_select_shape_color',
    'gl_object_mode_shape_color',
    'object_split_normals'
)
xray_custom_properties = (
    'object_flags',
    'object_userdata',
    'object_lod_reference',
    'object_owner_name',
    'object_creation_time',
    'object_modif_name',
    'object_modified_time',
    'object_motion_references',

    'mesh_flags',

    'material_two_sided',
    'material_shader',
    'material_compile',
    'material_game_mtl',

    'bone_game_mtl',
    'bone_length',
    'bone_shape_flags',
    'bone_shape_type',
    'bone_part',

    'bone_box_shape_rotation',
    'bone_box_shape_translate',
    'bone_box_shape_half_size',

    'bone_sphere_shape_position',
    'bone_sphere_shape_radius',

    'bone_cylinder_shape_position',
    'bone_cylinder_shape_direction',
    'bone_cylinder_shape_hight',
    'bone_cylinder_shape_radius',

    'bone_ik_joint_type',

    'bone_limit_x_min',
    'bone_limit_x_max',
    'bone_limit_y_min',
    'bone_limit_y_max',
    'bone_limit_z_min',
    'bone_limit_z_max',

    'bone_limit_x_spring',
    'bone_limit_y_spring',
    'bone_limit_z_spring',

    'bone_limit_x_damping',
    'bone_limit_y_damping',
    'bone_limit_z_damping',

    'bone_spring',
    'bone_damping',

    'bone_mass',
    'bone_center_of_mass',

    'bone_ik_flags',
    'bone_breakable_force',
    'bone_breakable_torque',
    'bone_friction',

    'action_fps',
    'action_speed',
    'action_accrue',
    'action_falloff',
    'action_bone_part',
    'action_flags',
    'action_power'
)


def update_paths(prefs, context):
    not_found_paths = set()
    for path_prop, suffix in path_props_suffix_values.items():
        if getattr(prefs, path_prop):
            setattr(prefs, build_auto_id(path_prop), getattr(prefs, path_prop))
            continue
        prop_type = path_props_types[path_prop]
        if prop_type == DIRECTORY:
            cheker_function = os.path.isdir
        elif prop_type == FILE:
            cheker_function = os.path.isfile
        path_value, not_found = _auto_path(
            prefs,
            path_prop,
            suffix,
            cheker_function
        )
        if not_found:
            not_found_paths.add(os.path.abspath(not_found))
        if path_value and prop_type == DIRECTORY:
            if not path_value.endswith(os.sep):
                path_value += os.sep
        setattr(prefs, build_auto_id(path_prop), path_value)
    if not_found_paths:
        not_found_paths = list(not_found_paths)
        not_found_paths.sort()
        utils.draw.show_message(
            text.get_text(text.error.file_folder_not_found),
            not_found_paths,
            text.get_text(text.error.error_title),
            'ERROR'
        )


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
    'objects_folder'
]

fs_props = {
    'gamedata_folder': ('$game_data$', None),
    'textures_folder': ('$game_textures$', None),
    'meshes_folder': ('$game_meshes$', None),
    'levels_folder': ('$game_levels$', None),
    'gamemtl_file': ('$game_data$', 'gamemtl.xr'),
    'eshader_file': ('$game_data$', 'shaders.xr'),
    'cshader_file': ('$game_data$', 'shaders_xrlc.xr'),
    'objects_folder': ('$objects$', None)
}


def _auto_path(prefs, self_name, path_suffix, checker):
    if prefs.fs_ltx_file:
        if not os.path.exists(prefs.fs_ltx_file):
            return '', prefs.fs_ltx_file
        try:
            fs = rw.ltx.LtxParser()
            fs.from_file(prefs.fs_ltx_file)
        except:
            traceback.print_exc()
            utils.draw.show_message(
                text.get_text(text.error.ltx_invalid_syntax),
                (prefs.fs_ltx_file, sys.exc_info()[1]),
                text.get_text(text.error.error_title),
                'ERROR'
            )
            return '', False
        prop_key, file_name = fs_props[self_name]
        dir_path = fs.values[prop_key]
        if file_name:
            result = os.path.join(dir_path, file_name)
        else:
            result = dir_path
        return result, False
    for prop in __AUTO_PROPS__:
        if prop == self_name:
            continue
        value = getattr(prefs, prop)
        if not value:
            continue
        result = os.path.normpath(value)
        if prop != 'gamedata_folder':
            dirname = os.path.dirname(result)
            if prop == 'objects_folder':
                dirname = os.path.dirname(dirname)
                dirname = os.path.join(dirname, 'gamedata')
            if dirname == result:
                continue  # os.path.dirname('T:') == 'T:'
            result = dirname
        if path_suffix:
            result = os.path.join(result, path_suffix)
        if checker(result):
            if self_name == 'objects_folder':
                result = os.path.abspath(result)
            return result, False
        else:
            return '', result
    return '', False


path_props_suffix_values = {
    'gamedata_folder': '',
    'textures_folder': 'textures',
    'meshes_folder': 'meshes',
    'levels_folder': 'levels',
    'gamemtl_file': 'gamemtl.xr',
    'eshader_file': 'shaders.xr',
    'cshader_file': 'shaders_xrlc.xr',
    'objects_folder': os.path.join('..', 'rawdata', 'objects')
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
    'objects_folder': DIRECTORY
}


class XRayPrefsCustomProperties(bpy.types.PropertyGroup):
    # main
    category = bpy.props.EnumProperty(
        name='Custom Property Category',
        default='OBJECT',
        items=(
            ('OBJECT', 'Object', ''),
            ('MESH', 'Mesh', ''),
            ('MATERIAL', 'Material', ''),
            ('BONE', 'Bone', ''),
            ('ACTION', 'Action', '')
        )
    )
    bone_category = bpy.props.EnumProperty(
        name='Custom Property Bone Category',
        default='MAIN',
        items=(
            ('MAIN', 'Main', ''),
            ('SHAPE', 'Shape', ''),
            ('IK', 'IK', '')
        )
    )

    # object
    object_flags = bpy.props.StringProperty(
        name='Flags',
        default='flags'
    )
    object_userdata = bpy.props.StringProperty(
        name='Userdata',
        default='userdata'
    )
    object_lod_reference = bpy.props.StringProperty(
        name='LOD Reference',
        default='lod_reference'
    )
    object_owner_name = bpy.props.StringProperty(
        name='Owner Name',
        default='owner_name'
    )
    object_creation_time = bpy.props.StringProperty(
        name='Creation Time',
        default='creation_time'
    )
    object_modif_name = bpy.props.StringProperty(
        name='Modif Name',
        default='modif_name'
    )
    object_modified_time = bpy.props.StringProperty(
        name='Modified Time',
        default='modified_time'
    )
    object_motion_references = bpy.props.StringProperty(
        name='Motion References',
        default='motion_references'
    )

    # mesh
    mesh_flags = bpy.props.StringProperty(
        name='Flags',
        default='flags'
    )

    # material
    material_two_sided = bpy.props.StringProperty(
        name='Two Sided',
        default='two_sided'
    )
    material_shader = bpy.props.StringProperty(
        name='Shader',
        default='shader'
    )
    material_compile = bpy.props.StringProperty(
        name='Compile',
        default='compile'
    )
    material_game_mtl = bpy.props.StringProperty(
        name='Game Mtl',
        default='game_mtl'
    )

    # bone
    bone_game_mtl = bpy.props.StringProperty(
        name='Game Mtl',
        default='game_mtl'
    )
    bone_length = bpy.props.StringProperty(
        name='Length',
        default='length'
    )
    bone_shape_flags = bpy.props.StringProperty(
        name='Shape Flags',
        default='shape_flags'
    )
    bone_shape_type = bpy.props.StringProperty(
        name='Shape Type',
        default='shape_type'
    )
    bone_part = bpy.props.StringProperty(
        name='Bone Part',
        default='bone_part'
    )

    # box shape
    bone_box_shape_rotation = bpy.props.StringProperty(
        name='Box Shape Rotation',
        default='box_shape_rotation'
    )
    bone_box_shape_translate = bpy.props.StringProperty(
        name='Box Shape Translate',
        default='box_shape_translate'
    )
    bone_box_shape_half_size = bpy.props.StringProperty(
        name='Box Shape Half Size',
        default='box_shape_half_size'
    )

    # sphere shape
    bone_sphere_shape_position = bpy.props.StringProperty(
        name='Sphere Shape Position',
        default='sphere_shape_position'
    )
    bone_sphere_shape_radius = bpy.props.StringProperty(
        name='Sphere Shape Radius',
        default='sphere_shape_radius'
    )

    # cylinder shape
    bone_cylinder_shape_position = bpy.props.StringProperty(
        name='Cylinder Shape Position',
        default='cylinder_shape_position'
    )
    bone_cylinder_shape_direction = bpy.props.StringProperty(
        name='Cylinder Shape Direction',
        default='cylinder_shape_direction'
    )
    bone_cylinder_shape_hight = bpy.props.StringProperty(
        name='Cylinder Shape Hight',
        default='cylinder_shape_hight'
    )
    bone_cylinder_shape_radius = bpy.props.StringProperty(
        name='Cylinder Shape Radius',
        default='cylinder_shape_radius'
    )

    # ik joint type
    bone_ik_joint_type = bpy.props.StringProperty(
        name='IK Joint Type',
        default='ik_joint_type'
    )

    # limit
    bone_limit_x_min = bpy.props.StringProperty(
        name='Limit X Min',
        default='limit_x_min'
    )
    bone_limit_x_max = bpy.props.StringProperty(
        name='Limit X Max',
        default='limit_x_max'
    )
    bone_limit_y_min = bpy.props.StringProperty(
        name='Limit Y Min',
        default='limit_y_min'
    )
    bone_limit_y_max = bpy.props.StringProperty(
        name='Limit Y Max',
        default='limit_y_max'
    )
    bone_limit_z_min = bpy.props.StringProperty(
        name='Limit Z Min',
        default='limit_z_min'
    )
    bone_limit_z_max = bpy.props.StringProperty(
        name='Limit Z Max',
        default='limit_z_max'
    )

    # spring limit
    bone_limit_x_spring = bpy.props.StringProperty(
        name='Limit X Spring',
        default='limit_x_spring'
    )
    bone_limit_y_spring = bpy.props.StringProperty(
        name='Limit Y Spring',
        default='limit_y_spring'
    )
    bone_limit_z_spring = bpy.props.StringProperty(
        name='Limit Z Spring',
        default='limit_z_spring'
    )

    # damping limit
    bone_limit_x_damping = bpy.props.StringProperty(
        name='Limit X Damping',
        default='limit_x_damping'
    )
    bone_limit_y_damping = bpy.props.StringProperty(
        name='Limit Y Damping',
        default='limit_y_damping'
    )
    bone_limit_z_damping = bpy.props.StringProperty(
        name='Limit Z Damping',
        default='limit_z_damping'
    )

    # spring and damping
    bone_spring = bpy.props.StringProperty(
        name='Spring',
        default='spring'
    )
    bone_damping = bpy.props.StringProperty(
        name='Damping',
        default='damping'
    )

    # mass
    bone_mass = bpy.props.StringProperty(
        name='Mass',
        default='mass'
    )
    bone_center_of_mass = bpy.props.StringProperty(
        name='Center of Mass',
        default='center_of_mass'
    )

    # other
    bone_ik_flags = bpy.props.StringProperty(
        name='IK Flags',
        default='ik_flags'
    )
    bone_breakable_force = bpy.props.StringProperty(
        name='Breakable Force',
        default='breakable_force'
    )
    bone_breakable_torque = bpy.props.StringProperty(
        name='Breakable Torque',
        default='breakable_torque'
    )
    bone_friction = bpy.props.StringProperty(
        name='Friction',
        default='friction'
    )

    # action
    action_fps = bpy.props.StringProperty(
        name='FPS',
        default='fps'
    )
    action_speed = bpy.props.StringProperty(
        name='Speed',
        default='speed'
    )
    action_accrue = bpy.props.StringProperty(
        name='Accrue',
        default='accrue'
    )
    action_falloff = bpy.props.StringProperty(
        name='Falloff', 
        default='falloff'
    )
    action_bone_part = bpy.props.StringProperty(
        name='Bone Part',
        default='bone_part'
    )
    action_flags = bpy.props.StringProperty(
        name='Flags',
        default='flags'
    )
    action_power = bpy.props.StringProperty(
        name='Power',
        default='power'
    )


class XRAY_OT_add_keymap(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.add_keymap'
    bl_label = 'Add Keymap'

    operator = bpy.props.StringProperty()

    def execute(self, context):
        hotkeys.add_keymaps(only=self.operator)
        return {'FINISHED'}


classes = (
    XRAY_OT_add_keymap,
    XRayPrefsCustomProperties
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
