# pylint: disable=C0103

import bpy

from . import registry
from .ui import collapsible


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


def PropObjectBonesImportPretty():
    return bpy.props.BoolProperty(
        name='Import Pretty Bones',
        description='Skip IK limits and import a nice skeleton',
    )


def PropObjectBonesImportFake():
    return bpy.props.BoolProperty(
        name='Import Fake Bones',
        default=True,
        description='Create fake bones to connect real ones',
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


@registry.module_thing
class PluginPreferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    gamedata_folder = bpy.props.StringProperty(
        name='gamedata', description='The path to the \'gamedata\' directory',
        subtype='DIR_PATH')
    textures_folder = bpy.props.StringProperty(
        name='Textures Folder', description='The path to the \'gamedata/textures\' directory',
        subtype='DIR_PATH')
    gamemtl_file = bpy.props.StringProperty(
        name='GameMtl File', description='The path to the \'gamemtl.xr\' file',
        subtype='FILE_PATH')
    eshader_file = bpy.props.StringProperty(
        name='EShader File', description='The path to the \'shaders.xr\' file',
        subtype='FILE_PATH')
    cshader_file = bpy.props.StringProperty(
        name='CShader File', description='The path to the \'shaders_xrlc.xr\' file',
        subtype='FILE_PATH')
    expert_mode = bpy.props.BoolProperty(
        name='Expert Mode', description='Show additional properties/controls'
    )
    sdk_version = PropSDKVersion()
    object_motions_import = PropObjectMotionsImport()
    object_motions_export = PropObjectMotionsExport()
    object_mesh_split_by_mat = PropObjectMeshSplitByMaterials()
    object_texture_names_from_path = PropObjectTextureNamesFromPath()
    object_bones_custom_shapes = PropObjectBonesCustomShapes()
    object_bones_import_pretty = PropObjectBonesImportPretty()
    object_bones_import_fake = PropObjectBonesImportFake()
    anm_create_camera = PropAnmCameraAnimation()

    def get_textures_folder(self):
        result = self.textures_folder
        if not result and self.gamedata_folder:
            import os.path
            result = os.path.join(self.gamedata_folder, 'textures')
        return result

    def draw(self, _context):
        def prop_bool(layout, data, prop):
            # row = layout.row()
            # row.label(text=getattr(self.__class__, prop)[1]['name'] + ':')
            # row.prop(data, prop, text='')
            layout.prop(data, prop)

        layout = self.layout
        if not self.textures_folder and self.gamedata_folder:
            self.textures_folder = self.get_textures_folder()
        layout.prop(self, 'textures_folder', expand=True)
        layout.prop(self, 'gamemtl_file', emboss=True)
        layout.prop(self, 'eshader_file')
        layout.prop(self, 'cshader_file')

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
                prop_bool(box_n, self, 'object_bones_import_fake')
                prop_bool(box_n, self, 'object_bones_import_pretty')

            _, box_n = collapsible.draw(box, 'plugin_prefs:defaults.anm', 'Animation', style='tree')
            if box_n:
                prop_bool(box_n, self, 'anm_create_camera')

        prop_bool(layout, self, 'expert_mode')
