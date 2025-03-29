import bpy
import tests
import io_scene_xray


class TestOpsProps(tests.utils.XRayTestCase):

    def test_change_object_type(self):
        tests.utils.remove_all_objects()

        # tests without objects
        bpy.ops.io_scene_xray.change_object_type(mode='ACTIVE', obj_type='st')
        bpy.ops.io_scene_xray.change_object_type(mode='SELECTED', obj_type='st')
        bpy.ops.io_scene_xray.change_object_type(mode='ALL', obj_type='st')

        # Arrange
        active, selected = self._create_objects()

        self.default = {}
        for obj in bpy.data.objects:
            self.default[obj.name] = obj.xray.flags_simple

        # Act
        bpy.ops.io_scene_xray.change_object_type(mode='ACTIVE', obj_type='dy')

        # Assert
        self.assertEqual(active.xray.flags_simple, 'dy')
        for obj in bpy.data.objects:
            if obj == active:
                continue
            self.assertEqual(obj.xray.flags_simple, self.default[obj.name])
        self._reset_objects_type()

        # Act
        bpy.ops.io_scene_xray.change_object_type(mode='SELECTED', obj_type='ho')

        # Assert
        for obj in selected:
            self.assertEqual(obj.xray.flags_simple, 'ho')
        for obj in bpy.data.objects:
            if obj in selected:
                continue
            self.assertEqual(obj.xray.flags_simple, self.default[obj.name])
        self._reset_objects_type()

        # Act
        bpy.ops.io_scene_xray.change_object_type(mode='ALL', obj_type='mu')

        # Assert
        for obj in bpy.data.objects:
            self.assertEqual(obj.xray.flags_simple, 'mu')
        self._reset_objects_type()

        # tests without root-objects
        for obj in bpy.data.objects:
            obj.xray.isroot = False
        bpy.ops.io_scene_xray.change_object_type(mode='ACTIVE', obj_type='st')
        bpy.ops.io_scene_xray.change_object_type(mode='SELECTED', obj_type='st')
        bpy.ops.io_scene_xray.change_object_type(mode='ALL', obj_type='st')

    def _reset_objects_type(self):
        for obj_name, obj_type in self.default.items():
            obj = bpy.data.objects[obj_name]
            obj.xray.flags_simple = obj_type

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
