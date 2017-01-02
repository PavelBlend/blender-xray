from tests import utils

import bpy
import re


class TestFormatObject(utils.XRayTestCase):
    def test_import_merge_materials_texture_case(self):
        # Arrange
        original_materials_count = len(bpy.data.materials)

        # Act
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_texture_caps.object'}],
        )
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_texture_caps.object'}],
        )

        # Assert
        self.assertEqual(len(bpy.data.materials), original_materials_count + 1)
