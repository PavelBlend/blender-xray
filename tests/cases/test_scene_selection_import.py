import os

import bpy

from tests import utils
from io_scene_xray import plugin_prefs


class TestSceneSelectionImport(utils.XRayTestCase):
    def test_default(self):
        prefs = plugin_prefs.get_preferences()
        prefs.objects_folder = os.path.join(os.curdir, 'tests', 'cases')

        # Act
        bpy.ops.xray_import.scene(filepath=os.path.join(self.relpath(), 'test_fmt.level'))

        # Assert
        self.assertReportsNotContains('WARNING')
