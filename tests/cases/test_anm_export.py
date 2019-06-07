from tests import utils

import bpy


class TestAnmExport(utils.XRayTestCase):
    def test_error_no_anim(self):
        # Arrange
        self._create_active_object()

        # Act & Assert
        with self.assertRaisesRegex(Exception, 'Object \'{}\' has no animation data'.format(bpy.context.object.name)):
            bpy.ops.xray_export.anm(
                filepath=self.outpath('test.anm'),
            )

    def test_error_yxz(self):
        # Arrange
        obj = self._create_active_object()
        act = bpy.data.actions.new('tact')
        obj.animation_data_create().action = act

        # Act & Assert
        with self.assertRaisesRegex(Exception, "Animation: rotation mode must be 'YXZ'"):
            bpy.ops.xray_export.anm(
                filepath=self.outpath('Cube1.anm'),
            )

    def test_ok(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        act = bpy.data.actions.new('tact')
        for i in range(3):
            fcu = act.fcurves.new('location', index=i)
            fcu.keyframe_points.insert(1, 0)
            fcu = act.fcurves.new('rotation_euler', index=i)
            fcu.keyframe_points.insert(1, 0)

        obj.animation_data_create().action = act

        # Act
        bpy.ops.xray_export.anm(
            filepath=self.outpath('test.anm'),
        )

        # Assert
        self.assertOutputFiles({
            'test.anm'
        })

    def _create_active_object(self):
        obj = bpy.data.objects.new('tobj', None)
        bpy.context.scene.objects.link(obj)
        bpy.context.scene.objects.active = obj
        return obj
