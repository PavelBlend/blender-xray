import os

import bpy

import io_scene_xray

from tests import utils


class TestLtxReading(utils.XRayTestCase):
    def test_paths(self):
        # Act
        ltx_folder = 'tests/cases'.replace('/', os.sep)
        ltx_name = 'test_fmt_path.ltx'
        ltx_path = os.path.join(ltx_folder, ltx_name)
        ltx = io_scene_xray.xray_ltx.StalkerLtxParser(ltx_path)

        self.assertEqual(ltx.values['$sdk_root$'], ltx_folder)
        self.assertEqual(
            ltx.values['$sdk_root_raw$'],
            os.path.join(ltx.values['$sdk_root$'], 'rawdata' + os.sep)
        )
        self.assertEqual(
            ltx.values['$game_textures$'],
            os.path.join(ltx.values['$sdk_root_raw$'], 'textures' + os.sep)
        )
        self.assertEqual(
            ltx.values['$objects$'],
            os.path.join(ltx.values['$sdk_root_raw$'], 'objects' + os.sep)
        )

    def test_config(self):
        # Act
        file_path = 'tests\\cases\\test_fmt_config.ltx'
        ltx = io_scene_xray.xray_ltx.StalkerLtxParser(file_path)
