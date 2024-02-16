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
