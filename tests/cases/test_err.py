import bpy
import tests


class TestErrImport(tests.utils.XRayTestCase):
    def test_default(self):
        # Act
        bpy.ops.xray_import.err(filepath=self.binpath('test_fmt.err'))

        # Arrange
        obj = bpy.data.objects['test_fmt.err']
        faces_count = len(obj.data.polygons)

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertNotEqual(faces_count, 0)

    def test_sdk_err_format(self):
        # Act
        bpy.ops.xray_import.err(filepath=self.binpath('test_fmt_sdk.err'))

        # Arrange
        obj = bpy.data.objects['test_fmt_sdk.err']
        faces_count = len(obj.data.polygons)

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertNotEqual(faces_count, 0)
