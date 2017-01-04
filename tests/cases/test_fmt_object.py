from tests import utils

import bpy
import re


class TestFormatObject(utils.XRayTestCase):
    def test_import_sg_maya(self):
        # Act
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_sg_maya.object'}],
        )

        # Assert
        data = bpy.data.meshes[-1]
        self.assertEqual(len(data.edges), 6)
        self.assertEqual(len([e for e in data.edges if e.use_edge_sharp]), 5)

    def test_import_sg_new(self):
        # Act
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            fmt_version='cscop',
            files=[{'name': 'test_fmt_sg_new.object'}],
        )

        # Assert
        data = bpy.data.meshes[-1]
        self.assertEqual(len(data.edges), 6)
        self.assertEqual(len([e for e in data.edges if e.use_edge_sharp]), 5)

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
