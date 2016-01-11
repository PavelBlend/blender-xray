import bpy


def get_preferences():
    return bpy.context.user_preferences.addons['io_scene_xray'].preferences


class PluginPreferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    gamedata_folder = bpy.props.StringProperty(name='gamedata', description='The path to the \'gamedata\' directory', subtype='DIR_PATH')
    textures_folder = bpy.props.StringProperty(name='textures', description='The path to the \'gamedata/textures\' directory', subtype='DIR_PATH')
    gamemtl_file = bpy.props.StringProperty(name='gamemtl', description='The path to the \'gamemtl.xr\' file', subtype='FILE_PATH')
    eshader_file = bpy.props.StringProperty(name='eshader', description='The path to the \'shaders.xr\' file', subtype='FILE_PATH')
    cshader_file = bpy.props.StringProperty(name='cshader', description='The path to the \'shaders_xrlc.xr\' file', subtype='FILE_PATH')

    def get_textures_folder(self):
        result = self.textures_folder;
        if not result and self.gamedata_folder:
            import os.path
            result = os.path.join(self.gamedata_folder, 'textures')
        return result

    def draw(self, context):
        layout = self.layout
        if not self.textures_folder and self.gamedata_folder:
            self.textures_folder = self.get_textures_folder()
        layout.prop(self, 'textures_folder', expand=True)
        layout.prop(self, 'gamemtl_file', emboss=True)
        layout.prop(self, 'eshader_file')
        layout.prop(self, 'cshader_file')
