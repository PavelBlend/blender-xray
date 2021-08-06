import os

import bpy

from tests import utils


class TestLevel(utils.XRayTestCase):
    def test_default(self):
        prefs = utils.get_preferences()
        prefs.gamemtl_file = os.path.join(self.relpath(), 'gamemtl.xr')

        # Import
        bpy.ops.xray_import.level(filepath=os.path.join(
            self.relpath(), 'test_fmt_level', 'level'
        ))

        # Export
        level_obj = bpy.data.objects['test_fmt_level']

        if bpy.app.version >= (2, 80, 0):
            level_obj.select_set(True)
        else:
            level_obj.select = True

        directory = self.outpath('test_fmt_level_export')
        if not os.path.exists(directory):
            os.makedirs(directory)
        utils.set_active_object(level_obj)
        bpy.ops.xray_export.level(directory=directory)

        # Assert
        self.assertReportsNotContains('WARNING')
