import bpy
import bmesh
import mathutils
import tests


class TestOpsMesh(tests.utils.XRayTestCase):

    def test_sel_verts_by_weights_general(self):
        # Arrange
        vertex_groups = (
            (),
            (0, ),
            (0, 1),
            (0, 1, 2),
            (0, 1, 2, 3),
            (0, 1, 2, 3, 4),
            (0, 1, 2, 3, 4, 5),
            (0, 1, 2, 3, 4, 5, 6, 7)
        )

        self.obj_1 = self._create_mesh_object(vertex_groups)
        self.obj_2 = self._create_mesh_object(vertex_groups)

        # Act
        self._select_objs()
        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='ACTIVE_OBJECT',
            weights_count=0,
            sel_type='EQUAL'
        )
        self.assertEqual(self._get_sel_verts_count(bpy.context.active_object), 3)

        self._select_objs()
        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='ACTIVE_OBJECT',
            weights_count=1,
            sel_type='EQUAL'
        )
        self.assertEqual(self._get_sel_verts_count(bpy.context.active_object), 1)

        self._select_objs()
        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='ACTIVE_OBJECT',
            weights_count=2,
            sel_type='EQUAL'
        )
        self.assertEqual(self._get_sel_verts_count(bpy.context.active_object), 1)

        self._select_objs()
        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='ACTIVE_OBJECT',
            weights_count=3,
            sel_type='EQUAL'
        )
        self.assertEqual(self._get_sel_verts_count(bpy.context.active_object), 1)

        self._select_objs()
        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='ACTIVE_OBJECT',
            weights_count=4,
            sel_type='EQUAL'
        )
        self.assertEqual(self._get_sel_verts_count(bpy.context.active_object), 1)

        self._select_objs()
        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='ACTIVE_OBJECT',
            weights_count=5,
            sel_type='EQUAL'
        )
        self.assertEqual(self._get_sel_verts_count(bpy.context.active_object), 1)

        self._select_objs()
        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='ALL_OBJECTS',
            weights_count=2,
            sel_type='EQUAL'
        )
        self.assertEqual(self._get_sel_verts_count(self.obj_1), 1)
        self.assertEqual(self._get_sel_verts_count(self.obj_2), 1)

        self._select_objs()
        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='SELECTED_OBJECTS',
            weights_count=2,
            sel_type='EQUAL'
        )
        self.assertEqual(self._get_sel_verts_count(self.obj_1), 1)
        self.assertEqual(self._get_sel_verts_count(self.obj_2), 1)

        self._select_objs()
        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='ACTIVE_OBJECT',
            weights_count=5,
            sel_type='LESS'
        )
        self.assertEqual(self._get_sel_verts_count(bpy.context.active_object), 7)

        self._select_objs()
        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='ACTIVE_OBJECT',
            weights_count=2,
            sel_type='GREATER'
        )
        self.assertEqual(self._get_sel_verts_count(bpy.context.active_object), 3)

        self._select_objs()
        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='ACTIVE_OBJECT',
            weights_count=2,
            sel_type='NOT_EQUAL'
        )
        self.assertEqual(self._get_sel_verts_count(bpy.context.active_object), 7)

    def test_sel_verts_by_weights_without_obj(self):
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)

        bpy.ops.io_scene_xray.sel_verts_by_weights(
            mode='ALL_OBJECTS',
            weights_count=4,
            sel_type='EQUAL'
        )

    def _get_sel_verts_count(self, obj):
        selected_count = 0
        for vert in obj.data.vertices: 
            if vert.select:
                selected_count += 1
        return selected_count

    def _select_objs(self):
        if bpy.context.active_object:
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        tests.utils.set_active_object(self.obj_1)
        tests.utils.select_object(self.obj_1)
        tests.utils.select_object(self.obj_2)

    def _create_mesh_object(self, vertex_groups):

        # create mesh and object
        mesh = bpy.data.meshes.new('test_mesh')
        obj = bpy.data.objects.new('test_mesh_obj', mesh)

        # link and select object
        tests.utils.link_object(obj)
        tests.utils.set_active_object(obj)
        tests.utils.select_object(obj)

        # create geometry
        bm = bmesh.new()
        bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=mathutils.Matrix.Identity(4),
            calc_uvs=True
        )
        bm.to_mesh(mesh)

        # bone names
        bone_names = tuple(('bone_{}'.format(i) for i in range(8)))

        # create vertex groups
        self._create_vertex_groups(obj, bone_names, vertex_groups)

        # create armature
        self._create_armature(obj, bone_names)

        return obj

    def _create_vertex_groups(self, obj, bone_names, vertex_groups):
        # create vertex groups
        for index, bone_name in enumerate(bone_names):
            vgroup = obj.vertex_groups.new(name=bone_name)
            vertex_group = vertex_groups[index]
            if vertex_group:
                vgroup.add(vertex_group, 1.0, 'REPLACE')

        # group without bone
        vgroup = obj.vertex_groups.new(name='group_without_bone')
        vgroup.add((0, 1, 2, 3), 1.0, 'REPLACE')

    def _create_armature(self, obj, bone_names):
        # create armature and object
        arm = bpy.data.armatures.new('test_arm')
        arm_obj = bpy.data.objects.new('test_arm_obj', arm)

        # link and select object
        tests.utils.link_object(arm_obj)
        tests.utils.set_active_object(arm_obj)
        tests.utils.select_object(arm_obj)

        # create bones
        bpy.ops.object.select_all(action='DESELECT')
        for index, bone_name in enumerate(bone_names):
            bpy.ops.object.mode_set(mode='EDIT')
            bone = arm_obj.data.edit_bones.new(bone_name)
            bone.head = (index, 0.0, 0.0)
            bone.tail = (index, 0.0, 1.0)
            bpy.ops.object.mode_set(mode='OBJECT')

        # set xray properties
        for index, bone in enumerate(arm_obj.data.bones):
            if index < 6:
                bone.xray.exportable = True
            else:
                bone.xray.exportable = False

        # set object parent
        obj.parent = arm_obj

        # add armature modifier
        mod = obj.modifiers.new('Armature', 'ARMATURE')
        mod.object = arm_obj

        # add empty armature modifier
        obj.modifiers.new('Armature 2', 'ARMATURE')

        # add any modifier
        obj.modifiers.new('Edge Split', 'EDGE_SPLIT')
