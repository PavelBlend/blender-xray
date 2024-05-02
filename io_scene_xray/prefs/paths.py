# blender modules
import bpy

# addon modules
from . import props
from .. import utils
from .. import formats


class PathsSettings(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    sdk_ver = formats.ie.PropSDKVersion()

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

    use_update = bpy.props.BoolProperty(default=True)


class XRAY_UL_path_presets_list(bpy.types.UIList):
    bl_idname = 'XRAY_UL_path_presets_list'

    def draw_item(
            self,
            context,
            layout,
            data,
            item,
            icon,
            active_data,
            active_propname,
            index
        ):

        if data.paths_presets_index == index:
            icon = 'CHECKBOX_HLT'
        else:
            icon = 'CHECKBOX_DEHLT'

        row = layout.row()
        row.label(text='', icon=icon)

        layout.prop(item, 'name', text='')


class PathsConfigs(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    platform = bpy.props.StringProperty()
    mod = bpy.props.StringProperty()


class XRAY_UL_path_configs_list(bpy.types.UIList):
    bl_idname = 'XRAY_UL_path_configs_list'

    def draw_item(
            self,
            context,
            layout,
            data,
            item,
            icon,
            active_data,
            active_propname,
            index
        ):

        if data.paths_configs_index == index:
            icon = 'CHECKBOX_HLT'
        else:
            icon = 'CHECKBOX_DEHLT'

        row = layout.row()
        row.label(text='', icon=icon)

        layout.prop(item, 'name', text='')


classes = (
    PathsSettings,
    PathsConfigs,
    XRAY_UL_path_presets_list,
    XRAY_UL_path_configs_list,
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
