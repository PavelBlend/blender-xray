from os.path import sep
from unittest.mock import patch

import bpy
from tests import utils

from io_scene_xray import prefs as addon_prefs


def np(path):
    return path.replace('/', sep)


def reset_settings(preferences):
    for prop_name in addon_prefs.props.__AUTO_PROPS__:
        preferences[prop_name] = ''
        preferences[prop_name + '_auto'] = ''


class TestPreferences(utils.XRayTestCase):
    def test_auto_values_default(self):
        prefs = utils.get_preferences()
        reset_settings(prefs)
        for prop in addon_prefs.props.__AUTO_PROPS__:
            self.assertEqual(getattr(prefs, prop), '', msg=prop)
            self.assertEqual(getattr(prefs, prop + '_auto'), '', msg=prop + '_auto')

    @patch('os.path.isfile', new=lambda path: path.endswith('.xr'))
    @patch('os.path.isdir', new=lambda path: path.endswith(np('/textures')))
    def test_auto_values_from_gamedata(self):
        prefs = utils.get_preferences()
        reset_settings(prefs)
        prefs.gamedata_folder = np('/gd')
        self.assertEqual(prefs.gamedata_folder, np('/gd'))
        self.assertEqual(prefs.gamedata_folder_auto, np('/gd'))
        self.assertEqual(prefs.textures_folder, '')
        self.assertEqual(prefs.textures_folder_auto, np('/gd/textures/'))
        self.assertEqual(prefs.gamemtl_file, '')
        self.assertEqual(prefs.gamemtl_file_auto, np('/gd/gamemtl.xr'))
        self.assertEqual(prefs.eshader_file, '')
        self.assertEqual(prefs.eshader_file_auto, np('/gd/shaders.xr'))
        self.assertEqual(prefs.cshader_file, '')
        self.assertEqual(prefs.cshader_file_auto, np('/gd/shaders_xrlc.xr'))

    @patch('os.path.isfile', new=lambda path: path.endswith('.xr'))
    @patch('os.path.isdir', new=lambda path: not path.endswith('.xr'))
    def test_auto_values_from_some_file(self):
        prefs = utils.get_preferences()
        reset_settings(prefs)
        prefs.gamemtl_file = np('/gdf/gamemtl.xr')
        self.assertEqual(prefs.gamedata_folder, '')
        self.assertEqual(prefs.gamedata_folder_auto, np('/gdf/'))
        self.assertEqual(prefs.textures_folder, '')
        self.assertEqual(prefs.textures_folder_auto, np('/gdf/textures/'))
        self.assertEqual(prefs.eshader_file, '')
        self.assertEqual(prefs.eshader_file_auto, np('/gdf/shaders.xr'))
        self.assertEqual(prefs.cshader_file, '')
        self.assertEqual(prefs.cshader_file_auto, np('/gdf/shaders_xrlc.xr'))

    @patch('os.path.isfile', new=lambda path: False)
    @patch('os.path.isdir', new=lambda path: False)
    def test_auto_values_if_no_paths(self):
        prefs = utils.get_preferences()
        reset_settings(prefs)
        prefs.textures_folder = np('/gdx/textures')
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
        prefs = utils.get_preferences()
        reset_settings(prefs)
        prefs.textures_folder = np('/gdr/textures')
        self.assertEqual(prefs.textures_folder, np('/gdr/textures'))
        self.assertEqual(prefs.gamemtl_file, '')
        self.assertEqual(prefs.gamemtl_file_auto, np('/gdr/gamemtl.xr'))

        prefs.gamemtl_file = prefs.gamemtl_file
        self.assertEqual(prefs.gamemtl_file, '')

        prefs.gamemtl_file = np('/gdr/gamemtl.xrx')
        self.assertEqual(prefs.gamemtl_file_auto, np('/gdr/gamemtl.xrx'))

    @patch('os.path.isdir', new=lambda path: path == np('/'))
    def test_auto_values_if_textures_is_root(self):
        prefs = utils.get_preferences()
        reset_settings(prefs)
        prefs.textures_folder = np('/')
        self.assertEqual(prefs.textures_folder, np('/'))
        self.assertEqual(prefs.textures_folder_auto, np('/'))
        self.assertEqual(prefs.gamedata_folder, '')
        self.assertEqual(prefs.gamedata_folder_auto, '')
        self.assertEqual(prefs.gamemtl_file, '')
        self.assertEqual(prefs.gamemtl_file_auto, '')
        self.assertEqual(prefs.eshader_file, '')
        self.assertEqual(prefs.eshader_file_auto, '')
        self.assertEqual(prefs.cshader_file, '')
        self.assertEqual(prefs.cshader_file_auto, '')

    def test_compact_menus(self):
        prefs = utils.get_preferences()
        prefs.compact_menus = True

    def test_formats_enable(self):
        prefs = utils.get_preferences()

        for value in (False, True):
            prefs.enable_object_import = value
            prefs.enable_object_export = value

            prefs.enable_skls_import = value
            prefs.enable_skls_export = value
            prefs.enable_skl_export = value

            prefs.enable_ogf_import = value
            prefs.enable_ogf_export = value

            prefs.enable_omf_import = value
            prefs.enable_omf_export = value

            prefs.enable_anm_import = value
            prefs.enable_anm_export = value

            prefs.enable_bones_import = value
            prefs.enable_bones_export = value

            prefs.enable_dm_import = value
            prefs.enable_dm_export = value

            prefs.enable_details_import = value
            prefs.enable_details_export = value

            prefs.enable_level_import = value
            prefs.enable_level_export = value

            prefs.enable_scene_import = value
            prefs.enable_scene_export = value

            prefs.enable_part_import = value

            prefs.enable_err_import = value

    def test_prefs_preset(self):
        bpy.ops.xray.prefs_preset_add(name='test_preset')
