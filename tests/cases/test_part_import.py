import os
import re
import bpy
import tests


class TestPartImport(tests.utils.XRayTestCase):
    def test_soc(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(self.binpath())

        # Act
        bpy.ops.xray_import.part(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_soc.part'}],
            fmt_version='soc'
        )

        # Assert
        self.assertReportsNotContains('ERROR')

    def test_cs_cop(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(self.binpath())

        # Act
        bpy.ops.xray_import.part(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_cs_cop.part'}],
            fmt_version='cscop'
        )

        # Assert
        self.assertReportsNotContains('ERROR')

    def test_without_objects(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(self.binpath())

        # Act
        bpy.ops.xray_import.part(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_empty.part'}],
            fmt_version='cscop'
        )

        # Assert
        self.assertReportsContains('ERROR', re.compile('File has no objects'))

    def test_no_exists_objects(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(self.binpath())

        # Act
        bpy.ops.xray_import.part(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_no_exists.part'}],
            fmt_version='cscop'
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('\[2x\] Cannot find file')
        )

    def test_broken(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(self.binpath())

        # Act
        bpy.ops.xray_import.part(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_broken.part'}],
            fmt_version='cscop'
        )

        # Assert
        self.assertReportsNotContains('ERROR')

    def test_export_path(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(
            os.path.dirname(self.binpath())
        )

        # Act
        bpy.ops.xray_import.part(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_export_path.part'}],
            fmt_version='cscop'
        )

        # Assert
        self.assertReportsNotContains('ERROR')
