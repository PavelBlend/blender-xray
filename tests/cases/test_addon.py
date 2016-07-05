from tests import utils

import bpy
import io_scene_xray


class TestAddon(utils.XRayTestCase):
    def test_blinfo(self):
        self.assertIsNotNone(io_scene_xray.bl_info)

    def test_enabled(self):
        self.assertIn('io_scene_xray', bpy.context.user_preferences.addons)

    def test_preferences(self):
        from io_scene_xray import plugin_prefs
        self.assertIsNotNone(plugin_prefs.get_preferences())
