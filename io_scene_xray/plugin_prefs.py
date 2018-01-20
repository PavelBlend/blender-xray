# pylint: disable=C0103
from os import path

import bpy

from . import registry
from .ui import collapsible
from .utils import with_auto_property


def get_preferences():
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


__AUTO_PROPS__ = [
    'gamedata_folder',
    'textures_folder',
    'gamemtl_file',
    'eshader_file',
    'cshader_file',
]
def _auto_path(obj, self_name, path_suffix, checker):
    for prop in __AUTO_PROPS__:
        if prop == self_name:
            continue
        value = getattr(obj, prop)
        if not value:
            continue
        result = path.normpath(value)
        if prop != 'gamedata_folder':
            result = path.dirname(result)
        if path_suffix:
            result = path.join(result, path_suffix)
        if checker(result):
            return result

    return ''


@registry.module_thing
@with_auto_property(
    bpy.props.StringProperty, 'gamedata_folder',
    lambda self: _auto_path(self, 'gamedata_folder', '', path.isdir),
    name='Gamedata Folder',
    description='Path to the \'gamedata\' directory',
    subtype='DIR_PATH',
)
@with_auto_property(
    bpy.props.StringProperty, 'textures_folder',
    lambda self: _auto_path(self, 'textures_folder', 'textures', path.isdir),
    name='Textures Folder',
    description='Path to the \'gamedata/textures\' directory',
    subtype='DIR_PATH',
)
@with_auto_property(
    bpy.props.StringProperty, 'gamemtl_file',
    lambda self: _auto_path(self, 'gamemtl_file', 'gamemtl.xr', path.isfile),
    name='GameMtl File',
    description='Path to the \'gamemtl.xr\' file',
    subtype='FILE_PATH',
)
@with_auto_property(
    bpy.props.StringProperty, 'eshader_file',
    lambda self: _auto_path(self, 'eshader_file', 'shaders.xr', path.isfile),
    name='EShader File',
    description='Path to the \'shaders.xr\' file',
    subtype='FILE_PATH',
)
@with_auto_property(
    bpy.props.StringProperty, 'cshader_file',
    lambda self: _auto_path(self, 'cshader_file', 'shaders_xrlc.xr', path.isfile),
    name='CShader File',
    description='Path to the \'shaders_xrlc.xr\' file',
    subtype='FILE_PATH',
)
class PluginPreferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    expert_mode = bpy.props.BoolProperty(
        name='Expert Mode', description='Show additional properties/controls'
    )
    sdk_version = PropSDKVersion()
    object_motions_import = PropObjectMotionsImport()
    object_motions_export = PropObjectMotionsExport()
    object_mesh_split_by_mat = PropObjectMeshSplitByMaterials()
    object_texture_names_from_path = PropObjectTextureNamesFromPath()
    object_bones_custom_shapes = PropObjectBonesCustomShapes()
    anm_create_camera = PropAnmCameraAnimation()

    def draw(self, _context):
        def prop_bool(layout, data, prop):
            # row = layout.row()
            # row.label(text=getattr(self.__class__, prop)[1]['name'] + ':')
            # row.prop(data, prop, text='')
            layout.prop(data, prop)

        def prop_auto(layout, data, prop):
            if not getattr(data, prop):
                nprop = prop + '_auto'
                if getattr(data, nprop):
                    prop = nprop
                    layout = layout.split()
                    layout.active = False
            layout.prop(data, prop)

        layout = self.layout
        prop_auto(layout, self, 'gamedata_folder')
        prop_auto(layout, self, 'textures_folder')
        prop_auto(layout, self, 'gamemtl_file')
        prop_auto(layout, self, 'eshader_file')
        prop_auto(layout, self, 'cshader_file')

        _, box = collapsible.draw(layout, 'plugin_prefs:defaults', 'Defaults', style='tree')
        if box:
            row = box.row()
            row.label('SDK Version:')
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

        prop_bool(layout, self, 'expert_mode')
