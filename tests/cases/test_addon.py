from tests import utils

import bpy
import io_scene_xray


class TestAddon(utils.XRayTestCase):
    def test_blinfo(self):
        self.assertIsNotNone(io_scene_xray.bl_info)

    def test_enabled(self):
        if bpy.app.version >= (2, 80, 0):
            self.assertIn('io_scene_xray', bpy.context.preferences.addons)
        else:
            self.assertIn('io_scene_xray', bpy.context.user_preferences.addons)
