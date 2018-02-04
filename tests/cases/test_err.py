import bpy

from tests import utils


class TestErrImport(utils.XRayTestCase):
    def test_default(self):
        # Act
        bpy.ops.xray_import.err(filepath=self.relpath('test_fmt.err'))

        # Assert
        self.assertReportsNotContains('WARNING')
