import re

import bpy

from tests import utils


class TestAnmImport(utils.XRayTestCase):
    def test_default(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.anm'}],
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertEqual(bpy.data.objects['test_fmt.anm.camera'].type, 'CAMERA')
        obj = bpy.data.objects['test_fmt.anm']
        act = obj.animation_data.action
        self.assertEqual(len(act.fcurves[0].keyframe_points), 3)

    def test_wo_camera(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.anm'}],
            camera_animation = False,
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertNotIn('test_fmt.anm.camera', bpy.data.objects)

    def test_has_no_chunk(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.object'}],
            camera_animation = False,
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('File has no main data block')
        )
