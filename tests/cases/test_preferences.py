from unittest.mock import patch

from tests import utils

from io_scene_xray import plugin_prefs

class TestPreferences(utils.XRayTestCase):
    def test_auto_values_default(self):
        prefs = plugin_prefs.get_preferences()
        for prop in plugin_prefs.__AUTO_PROPS__:
            self.assertEqual(getattr(prefs, prop), '', msg=prop)
            self.assertEqual(getattr(prefs, prop + '_auto'), '', msg=prop + '_auto')

    @patch('os.path.isfile', new=lambda path: path.endswith('.xr'))
    @patch('os.path.isdir', new=lambda path: path.endswith('/textures'))
    def test_auto_values_from_gamedata(self):
        prefs = plugin_prefs.get_preferences()
        prefs.gamedata_folder_auto = '/gd'
        self.assertEqual(prefs.gamedata_folder, '/gd')
        self.assertEqual(prefs.gamedata_folder_auto, '/gd')
        self.assertEqual(prefs.textures_folder, '')
        self.assertEqual(prefs.textures_folder_auto, '/gd/textures')
        self.assertEqual(prefs.gamemtl_file, '')
        self.assertEqual(prefs.gamemtl_file_auto, '/gd/gamemtl.xr')
        self.assertEqual(prefs.eshader_file, '')
        self.assertEqual(prefs.eshader_file_auto, '/gd/shaders.xr')
        self.assertEqual(prefs.cshader_file, '')
        self.assertEqual(prefs.cshader_file_auto, '/gd/shaders_xrlc.xr')

    @patch('os.path.isfile', new=lambda path: path.endswith('.xr'))
    @patch('os.path.isdir', new=lambda path: not path.endswith('.xr'))
    def test_auto_values_from_some_file(self):
        prefs = plugin_prefs.get_preferences()
        prefs.gamemtl_file_auto = '/gdf/gamemtl.xr'
        self.assertEqual(prefs.gamedata_folder, '')
        self.assertEqual(prefs.gamedata_folder_auto, '/gdf')
        self.assertEqual(prefs.textures_folder, '')
        self.assertEqual(prefs.textures_folder_auto, '/gdf/textures')
        self.assertEqual(prefs.eshader_file, '')
        self.assertEqual(prefs.eshader_file_auto, '/gdf/shaders.xr')
        self.assertEqual(prefs.cshader_file, '')
        self.assertEqual(prefs.cshader_file_auto, '/gdf/shaders_xrlc.xr')

    @patch('os.path.isfile', new=lambda path: False)
    @patch('os.path.isdir', new=lambda path: False)
    def test_auto_values_if_no_paths(self):
        prefs = plugin_prefs.get_preferences()
        prefs.textures_folder_auto = '/gdx/textures'
        self.assertEqual(prefs.gamedata_folder, '')
        self.assertEqual(prefs.gamedata_folder_auto, '')
        self.assertEqual(prefs.gamemtl_file, '')
        self.assertEqual(prefs.gamemtl_file_auto, '')
        self.assertEqual(prefs.eshader_file, '')
        self.assertEqual(prefs.eshader_file_auto, '')
        self.assertEqual(prefs.cshader_file, '')
        self.assertEqual(prefs.cshader_file_auto, '')

    @patch('os.path.isfile', new=lambda path: True)
    def test_auto_values_no_reassign(self):
        prefs = plugin_prefs.get_preferences()
        prefs.textures_folder_auto = '/gdr/textures'
        self.assertEqual(prefs.textures_folder, '/gdr/textures')
        self.assertEqual(prefs.gamemtl_file, '')
        self.assertEqual(prefs.gamemtl_file_auto, '/gdr/gamemtl.xr')

        prefs.gamemtl_file_auto = prefs.gamemtl_file_auto
        self.assertEqual(prefs.gamemtl_file, '')

        prefs.gamemtl_file_auto = '/gdr/gamemtl.xrx'
        self.assertEqual(prefs.gamemtl_file, '/gdr/gamemtl.xrx')

    @patch('os.path.isdir', new=lambda path: path == '/')
    def test_auto_values_if_textures_is_root(self):
        prefs = plugin_prefs.get_preferences()
        prefs.textures_folder = '/'
        self.assertEqual(prefs.textures_folder, '/')
        self.assertEqual(prefs.textures_folder_auto, '/')
        self.assertEqual(prefs.gamedata_folder, '')
        self.assertEqual(prefs.gamedata_folder_auto, '')
        self.assertEqual(prefs.gamemtl_file, '')
        self.assertEqual(prefs.gamemtl_file_auto, '')
        self.assertEqual(prefs.eshader_file, '')
        self.assertEqual(prefs.eshader_file_auto, '')
        self.assertEqual(prefs.cshader_file, '')
        self.assertEqual(prefs.cshader_file_auto, '')
