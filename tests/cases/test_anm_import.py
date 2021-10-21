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

    def test_v3(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_v3.anm'}],
            camera_animation=False,
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Motion shapes converted to LINEAR')
        )
        obj = bpy.data.objects['test_fmt_v3.anm']
        act = obj.animation_data.action
        self.assertEqual(act.frame_range[0], 0)
        self.assertEqual(act.frame_range[1], 20)

    def test_v4(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_v4.anm'}],
            camera_animation=False,
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Motion shapes converted to LINEAR')
        )
        obj = bpy.data.objects['test_fmt_v4.anm']
        act = obj.animation_data.action
        self.assertEqual(act.frame_range[0], 0)
        self.assertEqual(act.frame_range[1], 20)

    def test_wo_camera(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.anm'}],
            camera_animation=False,
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertNotIn('test_fmt.anm.camera', bpy.data.objects)

    def test_tcb(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_tcb.anm'}],
            camera_animation=False,
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Motion shapes converted to LINEAR')
        )

    def test_bezier_2d(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_bezier_2d.anm'}],
            camera_animation=False,
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Unsupported shapes are found, and will be replaced')
        )

    def test_has_no_chunk(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.object'}],
            camera_animation=False,
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('File has no main data block')
        )

    def test_file_not_found(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.relpath(),
            files=[{'name': 'not_found.anm'}],
            camera_animation=False,
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('File not found')
        )

    def test_name_and_linear(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_name_and_linear.anm'}],
            camera_animation=False,
        )

        obj = bpy.data.objects['test_name']
        act = obj.animation_data.action
        for i in range(6):
            self.assertEqual(len(act.fcurves[i].keyframe_points), 3)
            for key in act.fcurves[i].keyframe_points:
                self.assertEqual(key.interpolation, 'LINEAR')

        # Assert
        self.assertReportsNotContains('WARNING')
