import re
import bpy
import bmesh
import tests


class TestInvalidSG(tests.utils.XRayTestCase):
    def test_invalid_sg(self):
        # Arrange
        invalid_obj = self._create_object('invalid', True, False)
        correct_obj = self._create_object('correct', False, False)
        empty_obj = self._create_object('correct', True, True)

        # Act
        bpy.ops.io_scene_xray.check_invalid_sg_objs()

        # Assert
        self.assertReportsContains('INFO', re.compile('Ready'))

        selected = [obj for obj in bpy.context.selected_objects]
        self.assertEqual(selected, [invalid_obj, ])

    def test_incomp_sg(self):
        # run without objects
        bpy.ops.io_scene_xray.check_sg_incompatibility(mode='ACTIVE_OBJECT')

        # create bad object
        me_bad = bpy.data.meshes.new('bad')
        ob_bad = bpy.data.objects.new('bad', me_bad)

        # link and select bad object
        tests.utils.link_object(ob_bad)
        tests.utils.select_object(ob_bad)
        tests.utils.set_active_object(ob_bad)

        # add geometry
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1)
        bpy.ops.object.mode_set(mode='OBJECT')

        # set smoothing
        me_bad.edges[0].use_edge_sharp = True

        bpy.ops.object.select_all(action='DESELECT')

        # create correct object
        me_correct = bpy.data.meshes.new('correct')
        ob_correct = bpy.data.objects.new('correct', me_correct)

        # link and select correct object
        tests.utils.link_object(ob_correct)
        tests.utils.select_object(ob_correct)
        tests.utils.set_active_object(ob_correct)

        # add geometry
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.primitive_cube_add()
        bpy.ops.object.mode_set(mode='OBJECT')

        # set smoothing
        for edge in me_correct.edges:
            edge.use_edge_sharp = True

        bpy.ops.object.select_all(action='DESELECT')

        # create empty object
        ob_emp = bpy.data.objects.new('empty', None)

        # link empty object
        tests.utils.link_object(ob_emp)

        # select objects
        tests.utils.select_object(ob_bad)
        tests.utils.select_object(ob_correct)
        tests.utils.select_object(ob_emp)
        tests.utils.set_active_object(ob_correct)

        # Act
        bpy.ops.io_scene_xray.check_sg_incompatibility(mode='ACTIVE_OBJECT')

        # Assert
        self.assertEqual(len(bpy.context.selected_objects), 0)

        # select objects
        tests.utils.select_object(ob_bad)
        tests.utils.select_object(ob_correct)
        tests.utils.select_object(ob_emp)
        tests.utils.set_active_object(ob_correct)

        # Act
        bpy.ops.io_scene_xray.check_sg_incompatibility(mode='SELECTED_OBJECTS')

        # Assert
        self.assertEqual(len(bpy.context.selected_objects), 1)
        self.assertEqual(bpy.context.selected_objects[0].name, ob_bad.name)
        sharp_edges = [
            edge
            for edge in bpy.context.selected_objects[0].data.edges
                if edge.use_edge_sharp
        ]
        self.assertEqual(len(sharp_edges), 1)

        # select objects
        tests.utils.select_object(ob_bad)
        tests.utils.select_object(ob_correct)
        tests.utils.select_object(ob_emp)
        tests.utils.set_active_object(ob_correct)

        # Act
        bpy.ops.io_scene_xray.check_sg_incompatibility(mode='ALL_OBJECTS')

        # Assert
        self.assertEqual(len(bpy.context.selected_objects), 1)
        self.assertEqual(bpy.context.selected_objects[0].name, ob_bad.name)
        sharp_edges = [
            edge
            for edge in bpy.context.selected_objects[0].data.edges
                if edge.use_edge_sharp
        ]
        self.assertEqual(len(sharp_edges), 1)

    def _create_object(self, name, has_invalid_sg, empty):
        if empty:
            obj = bpy.data.objects.new(name, None)

        else:
            bm = bmesh.new()

            if has_invalid_sg:
                verts = (
                    (0.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0),
                    (1.0, 1.0, 0.0),
                    (0.5, 1.0, 0.0)
                )

                for coord in verts:
                    bm.verts.new(coord)
                bm.verts.ensure_lookup_table()

                faces = (
                    (0, 1, 2),
                    (3, 1, 0)
                )

                for face in faces:
                    bm_verts = []
                    for vert_index in face:
                        vert = bm.verts[vert_index]
                        bm_verts.append(vert)
                    bm.faces.new(bm_verts)

            else:
                bmesh.ops.create_cube(bm, size=2)

                for edge in bm.edges:
                    edge.smooth = False

            me = bpy.data.meshes.new(name)
            obj = bpy.data.objects.new(name, me)

            bm.to_mesh(me)

        tests.utils.link_object(obj)
        tests.utils.select_object(obj)

        return obj
