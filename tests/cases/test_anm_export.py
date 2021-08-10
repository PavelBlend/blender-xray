from tests import utils

import bpy


class TestAnmExport(utils.XRayTestCase):
    def test_yxz(self):
        # Arrange
        obj = self._create_active_object()
        act = bpy.data.actions.new('tact')
        obj.animation_data_create().action = act

        # Act
        bpy.ops.xray_export.anm(filepath=self.outpath('Cube1.anm'), )

        # Assert
        self.assertOutputFiles({
            'Cube1.anm'
        })

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
        utils.link_object(obj)
        utils.set_active_object(obj)
        return obj
