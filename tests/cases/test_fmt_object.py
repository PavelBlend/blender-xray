from tests import utils

import bpy
import re


class TestFormatObject(utils.XRayTestCase):
    def test_import_with_empty_polygons(self):
        # Act
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_invalid_face.object'}],
        )

        # Assert
        self.assertReportsContains('WARNING', re.compile('Mesh: invalid face found'))
