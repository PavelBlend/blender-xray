import re

import bpy

from tests import utils
from io_scene_xray.plugin import OpImportSkl

class TestSklImport(utils.XRayTestCase):
    def test_skl_no_bone(self):
        # Arrange
        self._create_armature('nobone')

        # Act
        bpy.ops.xray_import.skl(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.skl'}],
        )

        # Assert
        self.assertReportsContains('WARNING', re.compile('Bone is not found'))

    def test_skl(self):
        # Arrange
        self._create_armature('Bone')

        # Act
        bpy.ops.xray_import.skl(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.skl'}],
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertEqual(len(bpy.data.actions), 1)
        act = bpy.data.actions['test_fmt']
        self.assertEqual(len(act.fcurves[0].keyframe_points), 3)

    def test_skls(self):
        # Arrange
        self._create_armature('Bone')

        # Act
        bpy.ops.xray_import.skl(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.skls'}],
        )
        motions = list(OpImportSkl._examine_file(self.relpath('test_fmt.skls')))

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertEqual(len(bpy.data.actions), 1)
        act = bpy.data.actions['xact']
        self.assertEqual(len(act.fcurves[0].keyframe_points), 3)
        self.assertEqual(motions, ['xact'])

    def _create_armature(self, bone_name):
        arm = bpy.data.armatures.new('tarm')
        obj = bpy.data.objects.new('tobj', arm)
        bpy.context.scene.objects.link(obj)
        bpy.context.scene.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bone = arm.edit_bones.new(bone_name)
            bone.tail.y = 1
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
