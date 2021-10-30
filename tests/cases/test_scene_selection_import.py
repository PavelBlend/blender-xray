import os

import bpy

from tests import utils


class TestSceneSelectionImport(utils.XRayTestCase):
    def test_default(self):
        prefs = utils.get_preferences()
        prefs.objects_folder = os.path.join(os.curdir, 'tests', 'cases')

        # Act
        bpy.ops.xray_import.scene(filepath=os.path.join(self.relpath(), 'test_fmt.level'))

        # Assert
        self.assertReportsNotContains('WARNING')
