import bpy

from tests import utils


class TestErrImport(utils.XRayTestCase):
    def test_default(self):
        # Act
        bpy.ops.xray_import.err(filepath=self.binpath('test_fmt.err'))

        # Assert
        self.assertReportsNotContains('WARNING')

        obj = bpy.data.objects['test_fmt.err']
        self.assertNotEqual(len(obj.data.polygons), 0)

    def test_sdk_err_format(self):
        # Act
        bpy.ops.xray_import.err(filepath=self.binpath('test_fmt_sdk.err'))

        # Assert
        self.assertReportsNotContains('WARNING')

        obj = bpy.data.objects['test_fmt_sdk.err']
        self.assertNotEqual(len(obj.data.polygons), 0)
