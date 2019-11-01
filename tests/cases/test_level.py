import os

import bpy

from tests import utils
from io_scene_xray import plugin_prefs


class TestLevel(utils.XRayTestCase):
    def test_default(self):
        if bpy.app.version >= (2, 80, 0):
            prefs = plugin_prefs.get_preferences()
            prefs.gamemtl_file = os.path.join(self.relpath(), 'gamemtl.xr')

            # Import
            bpy.ops.xray_import.level(filepath=os.path.join(
                self.relpath(), 'test_fmt_level', 'level'
            ))

            # Export
            level_obj = bpy.data.objects['test_fmt_level']
            level_obj.select_set(True)
            directory = os.path.join(
                self.relpath(), 'test_fmt_level_export'
            )
            if not os.path.exists(directory):
                os.makedirs(directory)
            bpy.context.view_layer.objects.active = level_obj
            bpy.ops.xray_export.level(directory=directory)

            # Assert
            self.assertReportsNotContains('WARNING')
