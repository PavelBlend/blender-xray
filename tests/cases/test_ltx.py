import os
import io_scene_xray
import tests


class TestLtxReading(tests.utils.XRayTestCase):
    def test_paths(self):
        # Act
        ltx_folder = self.binpath()
        ltx_name = 'test_fmt_path.ltx'
        ltx_path = os.path.join(ltx_folder, ltx_name)
        ltx = io_scene_xray.rw.ltx.LtxParser()
        ltx.from_file(ltx_path)

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
        ltx_folder = self.binpath()
        ltx_name = 'test_fmt_config.ltx'
        ltx_path = os.path.join(ltx_folder, ltx_name)
        ltx = io_scene_xray.rw.ltx.LtxParser()
        ltx.from_file(ltx_path)
