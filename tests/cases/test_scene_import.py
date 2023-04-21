import os

import bpy

import tests


class TestSceneImport(tests.utils.XRayTestCase):
    def test_scene_import(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.join(os.curdir, 'tests', 'cases')

        # Act
        bpy.ops.xray_import.scene(
            filepath=os.path.join(self.binpath(), 'test_fmt.level')
        )

        # Assert
        self.assertReportsNotContains('WARNING')
