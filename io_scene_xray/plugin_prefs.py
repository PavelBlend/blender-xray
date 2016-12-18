import bpy


def get_preferences():
    return bpy.context.user_preferences.addons['io_scene_xray'].preferences


# noinspection PyPep8Naming
def PropSDKVersion():
    return bpy.props.EnumProperty(
        name='SDK Version',
        items=(('soc', 'SoC', ''), ('cscop', 'CS/CoP', ''))
    )


# noinspection PyPep8Naming
def PropObjectMotionsImport():
    return bpy.props.BoolProperty(
        name='Import Motions',
        description='Import embedded motions as actions',
        default=True
    )


# noinspection PyPep8Naming
def PropObjectMeshSplitByMaterials():
    return bpy.props.BoolProperty(
        name='Split Mesh By Materials',
        description='Import each surface (material) as separate set of faces',
        default=False
    )


# noinspection PyPep8Naming
def PropObjectMotionsExport():
    return bpy.props.BoolProperty(
        name='Export Motions',
        description='Export armatures actions as embedded motions',
        default=True
    )


# noinspection PyPep8Naming
def PropObjectTextureNamesFromPath():
    return bpy.props.BoolProperty(
        name='Texture Names From Image Paths',
        description='Generate texture names from image paths (by subtract <gamedata/textures> prefix and <file-extension> suffix)',
        default = True
    )


# noinspection PyPep8Naming
def PropObjectBonesCustomShapes():
    return bpy.props.BoolProperty(
        name='Custom Shapes For Bones',
        description='Use custom shapes for imported bones',
        default=True
    )


# noinspection PyPep8Naming
def PropObjectColorizeMaterials():
    return bpy.props.BoolProperty(
        name='Colorize Materials',
        description='Set a pseudo-random diffuse color for each surface (material)',
        default=False
    )


# noinspection PyPep8Naming
def PropAnmCameraAnimation():
    return bpy.props.BoolProperty(
        name='Create Linked Camera',
        description='Create animated camera object (linked to "empty"-object)',
        default = True
    )


# noinspection PyPep8Naming
def PropUseExportPaths():
    return bpy.props.BoolProperty(
        name='Use Export Paths',
        description='Append the Object.ExportPath to the export directory for each object',
        default=True
    )


class PluginPreferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    gamedata_folder = bpy.props.StringProperty(name='gamedata', description='The path to the \'gamedata\' directory', subtype='DIR_PATH')
    textures_folder = bpy.props.StringProperty(name='Textures Folder', description='The path to the \'gamedata/textures\' directory', subtype='DIR_PATH')
    gamemtl_file = bpy.props.StringProperty(name='GameMtl File', description='The path to the \'gamemtl.xr\' file', subtype='FILE_PATH')
    eshader_file = bpy.props.StringProperty(name='EShader File', description='The path to the \'shaders.xr\' file', subtype='FILE_PATH')
    cshader_file = bpy.props.StringProperty(name='CShader File', description='The path to the \'shaders_xrlc.xr\' file', subtype='FILE_PATH')
    expert_mode = bpy.props.BoolProperty(name='Expert Mode', description='Show additional properties/controls')
    sdk_version = PropSDKVersion()
    object_motions_import = PropObjectMotionsImport()
    object_motions_export = PropObjectMotionsExport()
    object_mesh_split_by_mat = PropObjectMeshSplitByMaterials()
    object_texture_names_from_path = PropObjectTextureNamesFromPath()
    object_bones_custom_shapes = PropObjectBonesCustomShapes()
    object_colorize_materials = PropObjectColorizeMaterials()
    anm_create_camera = PropAnmCameraAnimation()

    def get_textures_folder(self):
        result = self.textures_folder;
        if not result and self.gamedata_folder:
            import os.path
            result = os.path.join(self.gamedata_folder, 'textures')
        return result

    def draw(self, context):
        from .xray_inject_ui import draw_collapsible

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

        _, box = draw_collapsible(layout, 'plugin_prefs:defaults', 'Defaults', style='tree')
        if box:
            row = box.row()
            row.label('SDK Version:')
            row.prop(self, 'sdk_version', expand=True)

            _, bx = draw_collapsible(box, 'plugin_prefs:defaults.object', 'Object', style='tree')
            if bx:
                prop_bool(bx, self, 'object_motions_import')
                prop_bool(bx, self, 'object_motions_export')
                prop_bool(bx, self, 'object_texture_names_from_path')
                prop_bool(bx, self, 'object_mesh_split_by_mat')
                prop_bool(bx, self, 'object_bones_custom_shapes')
                prop_bool(bx, self, 'object_colorize_materials')

            _, bx = draw_collapsible(box, 'plugin_prefs:defaults.anm', 'Animation', style='tree')
            if bx:
                prop_bool(bx, self, 'anm_create_camera')

        prop_bool(layout, self, 'expert_mode')


def register():
    bpy.utils.register_class(PluginPreferences)


def unregister():
    bpy.utils.unregister_class(PluginPreferences)
