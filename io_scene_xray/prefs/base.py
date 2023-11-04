# blender modules
import bpy

# addon modules
from . import ui
from . import ops
from . import paths
from . import props
from . import preset
from .. import utils
from .. import menus
from .. import formats


def update_menu_func(self, context):
    menus.append_menu_func()


class XRayKeyMap(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    operator = bpy.props.StringProperty()


class XRAY_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    # path props
    fs_ltx_file = bpy.props.StringProperty(
        subtype='FILE_PATH',
        name='fs.ltx File',
        update=props.update_paths
    )
    gamedata_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=props.update_paths
    )
    textures_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=props.update_paths
    )
    meshes_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=props.update_paths
    )
    levels_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=props.update_paths
    )
    gamemtl_file = bpy.props.StringProperty(
        subtype='FILE_PATH',
        update=props.update_paths
    )
    eshader_file = bpy.props.StringProperty(
        subtype='FILE_PATH',
        update=props.update_paths
    )
    cshader_file = bpy.props.StringProperty(
        subtype='FILE_PATH',
        update=props.update_paths
    )
    objects_folder = bpy.props.StringProperty(
        subtype='DIR_PATH',
        update=props.update_paths
    )

    # path auto props
    gamedata_folder_auto = bpy.props.StringProperty()
    textures_folder_auto = bpy.props.StringProperty()
    meshes_folder_auto = bpy.props.StringProperty()
    levels_folder_auto = bpy.props.StringProperty()
    gamemtl_file_auto = bpy.props.StringProperty()
    eshader_file_auto = bpy.props.StringProperty()
    cshader_file_auto = bpy.props.StringProperty()
    objects_folder_auto = bpy.props.StringProperty()

    compact_menus = bpy.props.BoolProperty(
        name='Compact Import/Export Menus',
        update=update_menu_func
    )

    paths_mode = bpy.props.EnumProperty(
        default='BASE',
        items=(('BASE', 'Base', ''), ('ADVANCED', 'Advanced', ''))
    )

    # defaults
    defaults_category = bpy.props.EnumProperty(
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
            ('PART', 'Part', '')
        )
    )

    # object import props
    sdk_version = formats.ie.PropSDKVersion()
    object_motions_import = formats.ie.PropObjectMotionsImport()
    object_mesh_split_by_mat = formats.ie.PropObjectMeshSplitByMaterials()

    # object export props
    export_object_sdk_version = formats.ie.PropSDKVersion()
    smoothing_out_of = formats.ie.prop_smoothing_out_of()
    object_motions_export = formats.ie.PropObjectMotionsExport()
    object_texture_names_from_path = formats.ie.PropObjectTextureNamesFromPath()
    export_object_use_export_paths = formats.ie.PropUseExportPaths()

    # anm import props
    anm_create_camera = formats.ie.PropAnmCameraAnimation()

    # anm export props
    anm_format_version = formats.ie.prop_anm_format_version()

    # skl/skls import props
    add_to_motion_list = formats.ie.prop_skl_add_actions_to_motion_list()

    # bones import props
    bones_import_bone_parts = formats.ie.prop_import_bone_parts()
    bones_import_bone_properties = formats.ie.prop_import_bone_properties()

    # bones export props
    bones_export_bone_parts = formats.ie.prop_export_bone_parts()
    bones_export_bone_properties = formats.ie.prop_export_bone_properties()

    # details import props
    details_models_in_a_row = formats.ie.prop_details_models_in_a_row()
    load_slots = formats.ie.prop_details_load_slots()
    details_format = formats.ie.prop_details_format()

    # details export props
    details_texture_names_from_path = formats.ie.PropObjectTextureNamesFromPath()
    format_version = formats.ie.prop_details_format_version()

    # dm export props
    dm_texture_names_from_path = formats.ie.PropObjectTextureNamesFromPath()

    # ogf import props
    ogf_import_motions = formats.ie.PropObjectMotionsImport()

    # ogf export props
    ogf_texture_names_from_path = formats.ie.PropObjectTextureNamesFromPath()
    ogf_export_motions = formats.ie.PropObjectMotionsExport()
    ogf_export_fmt_ver = formats.ie.PropSDKVersion()
    ogf_export_hq_motions = formats.ie.prop_omf_high_quality()
    ogf_export_use_export_paths = formats.ie.PropUseExportPaths()

    # omf import props
    omf_import_motions = formats.ie.PropObjectMotionsImport()
    import_bone_parts = formats.ie.prop_import_bone_parts()
    omf_add_actions_to_motion_list = formats.ie.prop_skl_add_actions_to_motion_list()

    # omf export props
    omf_export_bone_parts = formats.ie.prop_export_bone_parts()
    omf_export_mode = formats.ie.prop_omf_export_mode()
    omf_motions_export = formats.ie.PropObjectMotionsExport()
    omf_high_quality = formats.ie.prop_omf_high_quality()

    # scene selection import props
    scene_selection_sdk_version = formats.ie.PropSDKVersion()
    scene_selection_mesh_split_by_mat = formats.ie.PropObjectMeshSplitByMaterials()

    # part import props
    part_sdk_version = formats.ie.PropSDKVersion()
    part_mesh_split_by_mat = formats.ie.PropObjectMeshSplitByMaterials()

    # keymap
    keymaps_collection = bpy.props.CollectionProperty(type=XRayKeyMap)
    keymaps_collection_index = bpy.props.IntProperty(options={'SKIP_SAVE'})

    # enable import plugins
    enable_object_import = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_anm_import = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_dm_import = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_details_import = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_skls_import = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_bones_import = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_err_import = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_scene_import = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_level_import = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_omf_import = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_ogf_import = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_part_import = bpy.props.BoolProperty(default=True, update=update_menu_func)

    # enable export plugins
    enable_object_export = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_anm_export = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_dm_export = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_details_export = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_skls_export = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_skl_export = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_bones_export = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_scene_export = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_level_export = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_omf_export = bpy.props.BoolProperty(default=True, update=update_menu_func)
    enable_ogf_export = bpy.props.BoolProperty(default=True, update=update_menu_func)

    category = bpy.props.EnumProperty(
        default='PATHS',
        items=(
            ('PATHS', 'Paths', ''),
            ('DEFAULTS', 'Defaults', ''),
            ('PLUGINS', 'Formats', ''),
            ('KEYMAP', 'Keymap', ''),
            ('CUSTOM_PROPS', 'Custom Props', ''),
            ('OTHERS', 'Others', '')
        )
    )

    custom_props = bpy.props.PointerProperty(type=props.XRayPrefsCustomProperties)
    custom_owner_name = bpy.props.StringProperty()

    # viewport props
    gl_shape_color = bpy.props.FloatVectorProperty(
        name='Unselected Shape',
        default=(0.0, 0.0, 1.0, 0.5),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    )
    gl_active_shape_color = bpy.props.FloatVectorProperty(
        name='Active Shape',
        default=(1.0, 1.0, 1.0, 0.7),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    )
    gl_select_shape_color = bpy.props.FloatVectorProperty(
        name='Selected Shape',
        default=(0.0, 1.0, 1.0, 0.7),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    )
    gl_object_mode_shape_color = bpy.props.FloatVectorProperty(
        name='Shape in Object Mode',
        default=(0.8, 0.8, 0.8, 0.8),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    )

    # custom data props
    object_split_normals = bpy.props.BoolProperty(
        name='Use *.object Split Normals',
        default=False
    )

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


classes = (XRayKeyMap, XRAY_addon_preferences)


def register():
    utils.version.register_operators(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
