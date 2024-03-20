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


def update_menu_func(self, context):
    menus.append_menu_func()


def update_paths(prefs, context):
    if not prefs.use_update:
        return

    not_found_paths = set()

    for prop, suffix in path_props_suffix_values.items():

        if getattr(prefs, prop):
            setattr(prefs, build_auto_id(prop), getattr(prefs, prop))
            continue

        prop_type = path_props_types[prop]

        if prop_type == DIRECTORY:
            cheker_fun = os.path.isdir
        elif prop_type == FILE:
            cheker_fun = os.path.isfile

        try:
            value, not_found = _auto_path(prefs, prop, suffix, cheker_fun)
        except:
            return

        if not_found:
            not_found_paths.add(os.path.abspath(not_found))

        if value and prop_type == DIRECTORY:
            if not value.endswith(os.sep):
                value += os.sep

        setattr(prefs, build_auto_id(prop), value)

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
    'objects_folder': bpy.props.StringProperty(
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
    'objects_folder_auto': bpy.props.StringProperty(),

    'compact_menus': bpy.props.BoolProperty(
        name='Compact Import/Export Menus',
        update=update_menu_func
    ),
    'check_updates': bpy.props.BoolProperty(
        default=True,
        name='Check for Updates after Starting Blender'
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
    'sdk_version': formats.ie.PropSDKVersion(),
    'object_motions_import': formats.ie.PropObjectMotionsImport(),
    'object_mesh_split_by_mat': formats.ie.PropObjectMeshSplitByMaterials(),

    # object export props
    'export_object_sdk_version': formats.ie.PropSDKVersion(),
    'smoothing_out_of': formats.ie.prop_smoothing_out_of(),
    'object_motions_export': formats.ie.PropObjectMotionsExport(),
    'object_texture_names_from_path': formats.ie.PropObjectTextureNamesFromPath(),
    'export_object_use_export_paths': formats.ie.PropUseExportPaths(),

    # anm import props
    'anm_create_camera': formats.ie.PropAnmCameraAnimation(),

    # anm export props
    'anm_format_version': formats.ie.prop_anm_format_version(),

    # skl/skls import props
    'add_to_motion_list': formats.ie.prop_skl_add_actions_to_motion_list(),

    # bones import props
    'bones_import_bone_parts': formats.ie.prop_import_bone_parts(),
    'bones_import_bone_properties': formats.ie.prop_import_bone_properties(),

    # bones export props
    'bones_export_bone_parts': formats.ie.prop_export_bone_parts(),
    'bones_export_bone_properties': formats.ie.prop_export_bone_properties(),

    # details import props
    'details_models_in_a_row': formats.ie.prop_details_models_in_a_row(),
    'load_slots': formats.ie.prop_details_load_slots(),
    'details_format': formats.ie.prop_details_format(),

    # details export props
    'details_texture_names_from_path': formats.ie.PropObjectTextureNamesFromPath(),
    'format_version': formats.ie.prop_details_format_version(),

    # dm export props
    'dm_texture_names_from_path': formats.ie.PropObjectTextureNamesFromPath(),

    # ogf import props
    'ogf_import_motions': formats.ie.PropObjectMotionsImport(),

    # ogf export props
    'ogf_texture_names_from_path': formats.ie.PropObjectTextureNamesFromPath(),
    'ogf_export_motions': formats.ie.PropObjectMotionsExport(),
    'ogf_export_fmt_ver': formats.ie.PropSDKVersion(),
    'ogf_export_hq_motions': formats.ie.prop_omf_high_quality(),
    'ogf_export_use_export_paths': formats.ie.PropUseExportPaths(),

    # omf import props
    'omf_import_motions': formats.ie.PropObjectMotionsImport(),
    'import_bone_parts': formats.ie.prop_import_bone_parts(),
    'omf_add_actions_to_motion_list': formats.ie.prop_skl_add_actions_to_motion_list(),

    # omf export props
    'omf_export_bone_parts': formats.ie.prop_export_bone_parts(),
    'omf_export_mode': formats.ie.prop_omf_export_mode(),
    'omf_motions_export': formats.ie.PropObjectMotionsExport(),
    'omf_high_quality': formats.ie.prop_omf_high_quality(),

    # scene selection import props
    'scene_selection_sdk_version': formats.ie.PropSDKVersion(),
    'scene_selection_mesh_split_by_mat': formats.ie.PropObjectMeshSplitByMaterials(),

    # part import props
    'part_sdk_version': formats.ie.PropSDKVersion(),
    'part_mesh_split_by_mat': formats.ie.PropObjectMeshSplitByMaterials(),

    # part export props
    'part_exp_sdk_ver': formats.ie.PropSDKVersion(),

    # group import props
    'group_sdk_ver': formats.ie.PropSDKVersion(),
    'group_split_by_mat': formats.ie.PropObjectMeshSplitByMaterials(),

    # keymap
    'keymaps_collection': bpy.props.CollectionProperty(type=XRayKeyMap),
    'keymaps_collection_index': bpy.props.IntProperty(options={'SKIP_SAVE'}),

    # enable import plugins
    'enable_object_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_anm_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_dm_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_details_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_skls_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_bones_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_err_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_scene_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_level_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_omf_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_ogf_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_part_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_group_import': bpy.props.BoolProperty(default=True, update=update_menu_func),

    # enable export plugins
    'enable_object_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_anm_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_dm_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_details_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_skls_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_skl_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_bones_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_scene_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_level_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_omf_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_ogf_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_part_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_group_export': bpy.props.BoolProperty(default=True, update=update_menu_func),

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


def _clear_paths():
    pref = utils.version.get_preferences()
    pref.use_update = False

    for prop in path_props_suffix_values.keys():
        setattr(pref, build_auto_id(prop), '')
        setattr(pref, prop, '')

    pref.use_update = True


def _auto_path(prefs, prop_name, suffix, checker):
    if prefs.fs_ltx_file:

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

        return result, False

    for prop in __AUTO_PROPS__:
        if prop == prop_name:
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
                continue    # os.path.dirname('T:') == 'T:'
            result = dirname
        if suffix:
            result = os.path.join(result, suffix)
        if checker(result):
            if prop_name == 'objects_folder':
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
    XRAY_OT_add_keymap,
    XRayPrefsCustomProperties
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
