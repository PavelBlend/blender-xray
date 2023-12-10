import os
import re
import bpy
import tests


class TestGroupImport(tests.utils.XRayTestCase):
    def test_import(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(self.binpath())

        # Act
        bpy.ops.xray_import.group(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.group'}],
            fmt_version='soc'
        )

        # Assert
        self.assertReportsNotContains('ERROR')
