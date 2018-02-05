import re

import bpy

from tests import utils
from io_scene_xray.plugin import OpImportSkl, BaseSelectMotionsOp

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

    def test_skl_filter(self):
        # Arrange
        self._create_armature('Bone')

        # Act
        bpy.ops.xray_import.skl(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.skl'}],
            motions=[{'name': 'test_fmt', 'flag': False}],
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertEqual(len(bpy.data.actions), 0)

    def test_skls_filter(self):
        # Arrange
        self._create_armature('Bone')

        # Act
        bpy.ops.xray_import.skl(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.skls'}],
            motions=[{'name': 'xact', 'flag': False}],
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertEqual(len(bpy.data.actions), 0)

    def test_list_ops(self):
        # Arrange
        class MList:
            def __init__(self):
                self.filter_name = ''
                self.use_filter_invert = False
        mlist = MList()
        BaseSelectMotionsOp.set_motions_list(mlist)
        class Motion:
            def __init__(self, name):
                self.flag = True
                self.name = name

        motions = [Motion(str(i)) for i in range(12)]
        class Data:
            def __init__(self, motions):
                self.motions = motions
        BaseSelectMotionsOp.set_data(Data(motions))
        bpy.data.actions.new('10')

        def deselected():
            return [m.name for m in motions if not m.flag]

        # Act & Assert
        self.assertEqual(deselected(), [], msg='true by default')

        bpy.ops.io_scene_xray.motions_deselect_duplicated()
        self.assertEqual(deselected(), ['10'], msg='10 is deselected')

        mlist.filter_name = '1'
        bpy.ops.io_scene_xray.motions_deselect()
        self.assertEqual(deselected(), ['1', '10', '11'], msg='some are deselected')

        mlist.filter_name = '0'
        mlist.use_filter_invert = True
        bpy.ops.io_scene_xray.motions_select()
        self.assertEqual(deselected(), ['10'], msg='only 10 is deselected')

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
