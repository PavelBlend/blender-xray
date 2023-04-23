import re
import bpy
import tests


class TestAnmImport(tests.utils.XRayTestCase):
    def test_default(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.anm'}]
        )

        # Arrange
        obj_root = bpy.data.objects['test_fmt.anm']
        obj_camera = bpy.data.objects['test_fmt.anm.camera']
        act = obj_root.animation_data.action

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertEqual(obj_camera.type, 'CAMERA')
        self.assertEqual(len(act.fcurves[0].keyframe_points), 3)

    def test_v3(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_v3.anm'}],
            camera_animation=False
        )

        # Arrange
        obj = bpy.data.objects['test_fmt_v3.anm']
        act = obj.animation_data.action

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Motion shapes converted to LINEAR')
        )
        self.assertEqual(act.frame_range[0], 0)
        self.assertEqual(act.frame_range[1], 20)

    def test_v4(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_v4.anm'}],
            camera_animation=False
        )

        # Arrange
        obj = bpy.data.objects['test_fmt_v4.anm']
        act = obj.animation_data.action

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Motion shapes converted to LINEAR')
        )
        self.assertEqual(act.frame_range[0], 0)
        self.assertEqual(act.frame_range[1], 20)

    def test_wo_camera(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.anm'}],
            camera_animation=False
        )

        # Assert
        self.assertReportsNotContains('WARNING')
        self.assertReportsNotContains('ERROR')
        self.assertNotIn('test_fmt.anm.camera', bpy.data.objects)

    def test_tcb(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_tcb.anm'}],
            camera_animation=False
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Motion shapes converted to LINEAR')
        )

    def test_bezier_2d(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_bezier_2d.anm'}],
            camera_animation=False
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Motion shapes converted to LINEAR')
        )

    def test_has_no_chunk(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.object'}],
            camera_animation=False
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('File has no main data block')
        )

    def test_file_not_found(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.binpath(),
            files=[{'name': 'not_found.anm'}],
            camera_animation=False
        )

        # Assert
        self.assertReportsContains('ERROR', re.compile('File not found'))

    def test_name_and_linear(self):
        # Act
        bpy.ops.xray_import.anm(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_name_and_linear.anm'}],
            camera_animation=False
        )

        # Arrange
        obj = bpy.data.objects['test_name']
        act = obj.animation_data.action

        # Assert
        for curve_index in range(6):
            keyframes = act.fcurves[curve_index].keyframe_points
            self.assertEqual(len(keyframes), 3)

            for key in keyframes:
                self.assertEqual(key.interpolation, 'LINEAR')

        self.assertReportsNotContains('WARNING')
