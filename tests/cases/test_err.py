import os

from tests import utils

import bpy


class TestErrImport(utils.XRayTestCase):
    def test_default(self):
        # Act
        bpy.ops.xray_import.err(
            filepath=self.relpath() + os.sep + 'test_fmt.err'
        )

        # Assert
        self.assertReportsNotContains('WARNING')
