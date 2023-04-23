import re
import bpy
import tests


class TestAnmExport(tests.utils.XRayTestCase):
    def test_xyz(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'XYZ'
        self._add_obj_action(obj, True, True, False)

        # Act
        bpy.ops.xray_export.anm_file(filepath=self.outpath('test_xyz.anm'))

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Object has rotation mode other than YXZ. Animation has been baked')
        )
        self.assertOutputFiles({'test_xyz.anm'})

    def test_has_no_rot(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        self._add_obj_action(obj, True, False, False)

        # Act
        bpy.ops.xray_export.anm_file(filepath=self.outpath('test.anm'))

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Action has keys not for all channels')
        )

    def test_has_no_loc(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        self._add_obj_action(obj, False, True, False)

        # Act
        bpy.ops.xray_export.anm_file(filepath=self.outpath('test.anm'))

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Action has keys not for all channels')
        )

    def test_has_no_loc_rot(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        act = bpy.data.actions.new('test_act')
        obj.animation_data_create().action = act

        # Act
        bpy.ops.xray_export.anm_file(filepath=self.outpath('test.anm'))

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Action has keys not for all channels')
        )

    def test_custom_refine(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        act = self._add_obj_action(obj, True, True, False)
        act.xray.autobake_custom_refine = True

        # Act
        bpy.ops.xray_export.anm_file(
            filepath=self.outpath('test_custom_refine.anm')
        )

        # Assert
        self.assertOutputFiles({'test_custom_refine.anm'})

    def test_bake_on(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        act = self._add_obj_action(obj, True, True, False)
        act.xray.autobake_custom_refine = True
        act.xray.autobake_on = True

        # Act
        bpy.ops.xray_export.anm_file(filepath=self.outpath('test_bake_on.anm'))

        # Assert
        self.assertOutputFiles({'test_bake_on.anm'})

    def test_color_keys(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        self._add_obj_action(obj, True, True, True)

        # Act
        bpy.ops.xray_export.anm_file(
            filepath=self.outpath('test_color_keys.anm')
        )

        # Assert
        self.assertOutputFiles({'test_color_keys.anm'})

    def test_ok(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        self._add_obj_action(obj, True, True, False)

        # Act
        bpy.ops.xray_export.anm_file(filepath=self.outpath('test_ok.anm'))

        # Assert
        self.assertOutputFiles({'test_ok.anm'})

    def test_v3(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        self._add_obj_action(obj, True, True, False)

        # Act
        bpy.ops.xray_export.anm_file(
            filepath=self.outpath('test_v3.anm'),
            format_version='3'
        )

        # Assert
        self.assertOutputFiles({'test_v3.anm'})

    def test_v4(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        self._add_obj_action(obj, True, True, False)

        # Act
        bpy.ops.xray_export.anm_file(
            filepath=self.outpath('test_v4.anm'),
            format_version='4'
        )

        # Assert
        self.assertOutputFiles({'test_v4.anm'})

    def test_v5(self):
        # Arrange
        obj = self._create_active_object()
        obj.rotation_mode = 'YXZ'
        self._add_obj_action(obj, True, True, False)

        # Act
        bpy.ops.xray_export.anm_file(
            filepath=self.outpath('test_v5.anm'),
            format_version='5'
        )

        # Assert
        self.assertOutputFiles({'test_v5.anm'})

    def test_batch(self):
        # Arrange
        out_files = set()
        for object_index in range(3):
            obj = self._create_active_object()
            obj_name = 'test_{}.anm'.format(object_index)
            obj.name = obj_name
            out_files.add(obj_name)
            obj.rotation_mode = 'YXZ'
            self._add_obj_action(obj, True, True, False)

        bpy.ops.object.select_all(action='SELECT')

        # Act
        bpy.ops.xray_export.anm(directory=self.outpath())

        # Assert
        self.assertOutputFiles(out_files)

    def _add_obj_action(self, obj, loc, rot, col):
        act = bpy.data.actions.new('test_act')
        obj.animation_data_create().action = act

        for axis_index in range(3):
            if loc:
                fcurve = act.fcurves.new('location', index=axis_index)
                fcurve.keyframe_points.insert(0, 0)
                fcurve.keyframe_points.insert(10, 1)

            if rot:
                fcurve = act.fcurves.new('rotation_euler', index=axis_index)
                fcurve.keyframe_points.insert(0, 0)
                fcurve.keyframe_points.insert(10, 1)

            if col:
                fcurve = act.fcurves.new('color', index=axis_index)
                fcurve.keyframe_points.insert(1, 0)
                fcurve.keyframe_points.insert(10, 1)

        return act

    def _create_active_object(self):
        obj = bpy.data.objects.new('test_obj', None)

        tests.utils.link_object(obj)
        tests.utils.set_active_object(obj)

        return obj
