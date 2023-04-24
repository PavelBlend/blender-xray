import os
import re
import bpy
import tests


class TestPartImport(tests.utils.XRayTestCase):
    def _test_part_import(self, file_name, ver):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(self.binpath())

        roots_count_before_import = self._get_roots_count()

        # Act
        bpy.ops.xray_import.part(
            directory=self.binpath(),
            files=[{'name': file_name}],
            fmt_version=ver
        )

        # Arrange
        roots_count_after_import = self._get_roots_count()

        roots_count = roots_count_after_import - roots_count_before_import

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertEqual(roots_count, 6)

    def test_soc(self):
        self._test_part_import('test_fmt_soc.part', 'soc')

    def test_cs_cop(self):
        self._test_part_import('test_fmt_cs_cop.part', 'cscop')

    def test_without_objects(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(self.binpath())

        roots_count_before_import = self._get_roots_count()

        # Act
        bpy.ops.xray_import.part(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_empty.part'}],
            fmt_version='cscop'
        )

        # Arrange
        roots_count_after_import = self._get_roots_count()

        roots_count = roots_count_after_import - roots_count_before_import

        # Assert
        self.assertReportsContains('ERROR', re.compile('File has no objects!'))
        self.assertEqual(roots_count, 0)

    def test_no_exists_objects(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(self.binpath())

        roots_count_before_import = self._get_roots_count()

        # Act
        bpy.ops.xray_import.part(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_no_exists.part'}],
            fmt_version='cscop'
        )

        # Arrange
        roots_count_after_import = self._get_roots_count()

        roots_count = roots_count_after_import - roots_count_before_import

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('\[2x\] Cannot find file')
        )
        self.assertEqual(roots_count, 0)

    def test_broken(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(self.binpath())

        roots_count_before_import = self._get_roots_count()

        # Act
        bpy.ops.xray_import.part(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_broken.part'}],
            fmt_version='cscop'
        )

        # Arrange
        roots_count_after_import = self._get_roots_count()

        roots_count = roots_count_after_import - roots_count_before_import

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertEqual(roots_count, 3)

    def test_export_path(self):
        prefs = tests.utils.get_preferences()
        prefs.objects_folder = os.path.abspath(
            os.path.dirname(self.binpath())
        )

        roots_count_before_import = self._get_roots_count()

        # Act
        bpy.ops.xray_import.part(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_export_path.part'}],
            fmt_version='cscop'
        )

        # Arrange
        roots_count_after_import = self._get_roots_count()

        roots_count = roots_count_after_import - roots_count_before_import

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertEqual(roots_count, 2)

        for obj_name in ('test_level_1.object', 'test_level_2.object'):
            obj = bpy.data.objects[obj_name]
            self.assertEqual(obj.xray.export_path, 'tested')

    def _get_roots_count(self):
        roots_count = 0
        for obj in bpy.data.objects:
            if obj.xray.isroot:
                roots_count += 1
        return roots_count
