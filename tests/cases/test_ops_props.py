import re
import bpy
import tests


class TestOpsProps(tests.utils.XRayTestCase):

    def test_change_object_type(self):
        tests.utils.remove_all_objects()

        # tests without objects

        self.clear_reports()
        bpy.ops.io_scene_xray.change_object_type(mode='ACTIVE', obj_type='st')
        self.assertReportsContains('ERROR', re.compile('No active object!'))

        self.clear_reports()
        bpy.ops.io_scene_xray.change_object_type(mode='SELECTED', obj_type='st')
        self.assertReportsContains('ERROR', re.compile('No selected objects!'))

        self.clear_reports()
        bpy.ops.io_scene_xray.change_object_type(mode='ALL', obj_type='st')
        self.assertReportsContains('ERROR', re.compile('Scene has no objects!'))

        # Arrange
        active, selected = self._create_objects()

        for obj in bpy.data.objects:
            obj.xray.flags_simple = 'st'

        self.default = {obj.name: obj.xray.flags_simple for obj in bpy.data.objects}

        # Act
        self.clear_reports()
        bpy.ops.io_scene_xray.change_object_type(mode='ACTIVE', obj_type='dy')
        self.assertReportsContains('INFO', re.compile('Objects Changed: 1'))

        # Assert
        self.assertEqual(active.xray.flags_simple, 'dy')
        for obj in bpy.data.objects:
            if obj == active:
                continue
            self.assertEqual(obj.xray.flags_simple, self.default[obj.name])
        self._reset_objects_type()

        # Act
        self.clear_reports()
        bpy.ops.io_scene_xray.change_object_type(mode='SELECTED', obj_type='ho')
        self.assertReportsContains('INFO', re.compile('Objects Changed: 2'))

        # Assert
        for obj in selected:
            self.assertEqual(obj.xray.flags_simple, 'ho')
        for obj in bpy.data.objects:
            if obj in selected:
                continue
            self.assertEqual(obj.xray.flags_simple, self.default[obj.name])
        self._reset_objects_type()

        # Act
        self.clear_reports()
        bpy.ops.io_scene_xray.change_object_type(mode='ALL', obj_type='mu')
        self.assertReportsContains('INFO', re.compile('Objects Changed: 5'))

        # Assert
        for obj in bpy.data.objects:
            self.assertEqual(obj.xray.flags_simple, 'mu')
        self._reset_objects_type()

        # tests without root-objects

        for obj in bpy.data.objects:
            obj.xray.isroot = False

        self.clear_reports()
        bpy.ops.io_scene_xray.change_object_type(mode='ACTIVE', obj_type='st')
        self.assertReportsContains('ERROR', re.compile('No root-objects!'))

        self.clear_reports()
        bpy.ops.io_scene_xray.change_object_type(mode='SELECTED', obj_type='st')
        self.assertReportsContains('ERROR', re.compile('No root-objects!'))

        self.clear_reports()
        bpy.ops.io_scene_xray.change_object_type(mode='ALL', obj_type='st')
        self.assertReportsContains('ERROR', re.compile('No root-objects!'))

    def test_change_hq_export(self):
        tests.utils.remove_all_objects()

        # tests without objects

        self.clear_reports()
        bpy.ops.io_scene_xray.change_hq_export(mode='ACTIVE', hq_export=True)
        self.assertReportsContains('ERROR', re.compile('No active object!'))

        self.clear_reports()
        bpy.ops.io_scene_xray.change_hq_export(mode='SELECTED', hq_export=True)
        self.assertReportsContains('ERROR', re.compile('No selected objects!'))

        self.clear_reports()
        bpy.ops.io_scene_xray.change_hq_export(mode='ALL', hq_export=True)
        self.assertReportsContains('ERROR', re.compile('Scene has no objects!'))

        # Arrange
        active, selected = self._create_objects()

        for obj in bpy.data.objects:
            obj.xray.flags_custom_hqexp = False

        self.default = {obj.name: obj.xray.flags_custom_hqexp for obj in bpy.data.objects}

        # Act
        self.clear_reports()
        bpy.ops.io_scene_xray.change_hq_export(mode='ACTIVE', hq_export=True)
        self.assertReportsContains('INFO', re.compile('Objects Changed: 1'))

        # Assert
        self.assertEqual(active.xray.flags_custom_hqexp, True)
        for obj in bpy.data.objects:
            if obj == active:
                continue
            self.assertEqual(obj.xray.flags_custom_hqexp, self.default[obj.name])
        self._reset_hq_export()

        # Act
        self.clear_reports()
        bpy.ops.io_scene_xray.change_hq_export(mode='SELECTED', hq_export=True)
        self.assertReportsContains('INFO', re.compile('Objects Changed: 2'))

        # Assert
        for obj in selected:
            self.assertEqual(obj.xray.flags_custom_hqexp, True)
        for obj in bpy.data.objects:
            if obj in selected:
                continue
            self.assertEqual(obj.xray.flags_custom_hqexp, self.default[obj.name])
        self._reset_hq_export()

        # Act
        self.clear_reports()
        bpy.ops.io_scene_xray.change_hq_export(mode='ALL', hq_export=True)
        self.assertReportsContains('INFO', re.compile('Objects Changed: 5'))

        # Assert
        for obj in bpy.data.objects:
            self.assertEqual(obj.xray.flags_custom_hqexp, True)
        self._reset_hq_export()

        # tests without root-objects

        for obj in bpy.data.objects:
            obj.xray.isroot = False

        self.clear_reports()
        bpy.ops.io_scene_xray.change_hq_export(mode='ACTIVE', hq_export=True)
        self.assertReportsContains('ERROR', re.compile('No root-objects!'))

        self.clear_reports()
        bpy.ops.io_scene_xray.change_hq_export(mode='SELECTED', hq_export=True)
        self.assertReportsContains('ERROR', re.compile('No root-objects!'))

        self.clear_reports()
        bpy.ops.io_scene_xray.change_hq_export(mode='ALL', hq_export=True)
        self.assertReportsContains('ERROR', re.compile('No root-objects!'))

    def _reset_objects_type(self):
        for obj_name, obj_type in self.default.items():
            obj = bpy.data.objects[obj_name]
            obj.xray.flags_simple = obj_type

    def _reset_hq_export(self):
        for obj_name, hq_exp in self.default.items():
            obj = bpy.data.objects[obj_name]
            obj.xray.flags_custom_hqexp = hq_exp

    def _create_objects(self):

        for i in range(5):
            bpy.ops.mesh.primitive_plane_add()

        bpy.ops.object.select_all(action='DESELECT')

        tests.utils.set_active_object(bpy.data.objects[0])
        active = bpy.data.objects[0]

        selected = []
        for i in (1, 2):
            tests.utils.select_object(bpy.data.objects[i])
            selected.append(bpy.data.objects[i])

        return active, selected
