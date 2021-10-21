import re

import bpy

from tests import utils


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


    def test_has_no_rot(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        act = bpy.data.actions.new('tact')
        for i in range(3):
            fcu = act.fcurves.new('location', index=i)
            fcu.keyframe_points.insert(1, 0)

        obj.animation_data_create().action = act

        # Act
        bpy.ops.xray_export.anm(
            filepath=self.outpath('test.anm'),
        )
        self.assertReportsContains('ERROR', re.compile('Action has keys not for all channels'))

    def test_has_no_loc(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        act = bpy.data.actions.new('tact')
        for i in range(3):
            fcu = act.fcurves.new('rotation_euler', index=i)
            fcu.keyframe_points.insert(1, 0)

        obj.animation_data_create().action = act

        # Act
        bpy.ops.xray_export.anm(
            filepath=self.outpath('test.anm'),
        )
        self.assertReportsContains('ERROR', re.compile('Action has keys not for all channels'))

    def test_has_no_loc_rot(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        act = bpy.data.actions.new('tact')
        obj.animation_data_create().action = act

        # Act
        bpy.ops.xray_export.anm(
            filepath=self.outpath('test.anm'),
        )
        self.assertReportsContains('ERROR', re.compile('Action has keys not for all channels'))

    def test_custom_refine(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        act = bpy.data.actions.new('tact')
        act.xray.autobake_custom_refine = True
        obj.animation_data_create().action = act

        for i in range(3):
            fcu = act.fcurves.new('location', index=i)
            fcu.keyframe_points.insert(1, 0)
            fcu.keyframe_points.insert(10, 1)
            fcu = act.fcurves.new('rotation_euler', index=i)
            fcu.keyframe_points.insert(1, 0)
            fcu.keyframe_points.insert(10, 1)

        # Act
        bpy.ops.xray_export.anm(
            filepath=self.outpath('test.anm'),
        )

    def test_bake_on(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        act = bpy.data.actions.new('tact')
        act.xray.autobake_custom_refine = True
        act.xray.autobake_on = True
        obj.animation_data_create().action = act

        for i in range(3):
            fcu = act.fcurves.new('location', index=i)
            fcu.keyframe_points.insert(1, 0)
            fcu.keyframe_points.insert(10, 1)
            fcu = act.fcurves.new('rotation_euler', index=i)
            fcu.keyframe_points.insert(1, 0)
            fcu.keyframe_points.insert(10, 1)

        # Act
        bpy.ops.xray_export.anm(
            filepath=self.outpath('test.anm'),
        )

    def test_color_keys(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        act = bpy.data.actions.new('tact')
        obj.animation_data_create().action = act

        for i in range(3):
            fcu = act.fcurves.new('location', index=i)
            fcu.keyframe_points.insert(1, 0)
            fcu.keyframe_points.insert(10, 1)
            fcu = act.fcurves.new('rotation_euler', index=i)
            fcu.keyframe_points.insert(1, 0)
            fcu.keyframe_points.insert(10, 1)
            fcu = act.fcurves.new('color', index=i)
            fcu.keyframe_points.insert(1, 0)
            fcu.keyframe_points.insert(10, 1)

        # Act
        bpy.ops.xray_export.anm(
            filepath=self.outpath('test.anm'),
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

    def test_v3(self):
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
            filepath=self.outpath('test_v3.anm'),
            format_version='3'
        )

        # Assert
        self.assertOutputFiles({
            'test_v3.anm'
        })

    def test_v4(self):
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
            filepath=self.outpath('test_v4.anm'),
            format_version='4'
        )

        # Assert
        self.assertOutputFiles({
            'test_v4.anm'
        })

    def test_v5(self):
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
            filepath=self.outpath('test_v5.anm'),
            format_version='5'
        )

        # Assert
        self.assertOutputFiles({
            'test_v5.anm'
        })

    def _create_active_object(self):
        obj = bpy.data.objects.new('tobj', None)
        utils.link_object(obj)
        utils.set_active_object(obj)
        return obj
