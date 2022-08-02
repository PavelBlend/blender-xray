import re

from tests import utils

import bpy


class TestDmExport(utils.XRayTestCase):
    def test_export_single(self):
        # Arrange
        self._create_dm_objects()

        # Act
        bpy.ops.xray_export.dm_file(
            detail_model='tdm1',
            filepath=self.outpath('test.dm'),
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'test.dm'
        })

    def test_vertices_count_limit(self):
        # Arrange
        self._create_dm_objects()

        # Subdivide geometry
        obj = bpy.data.objects['tdm1']
        utils.set_active_object(obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=70)
        bpy.ops.mesh.subdivide(number_cuts=2)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Act
        bpy.ops.xray_export.dm_file(
            detail_model='tdm1',
            filepath=self.outpath('test_vertices_count_limit.dm'),
            texture_name_from_image_path=False
        )
        self.assertReportsContains(
            'ERROR',
            re.compile('Mesh-object has too many vertices')
        )

    def _create_dm_objects(self, create_uv=True, create_material=True):
        bmesh = utils.create_bmesh((
            (0, 0, 0),
            (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0),
        ), ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)), create_uv)

        objs = []
        for i in range(3):
            obj = utils.create_object(bmesh, create_material)
            obj.name = 'tdm%d' % (i + 1)
            objs.append(obj)
            bpy_texture = bpy.data.textures.new('test_texture', 'IMAGE')
            bpy_image = bpy.data.images.new('test_image.dds', 0, 0)
            bpy_image.source = 'FILE'
            bpy_image.filepath = 'test_image.dds'
            if bpy.app.version >= (2, 80, 0):
                obj.data.materials[0].use_nodes = True
                node_tree = obj.data.materials[0].node_tree
                texture_node = node_tree.nodes.new('ShaderNodeTexImage')
                texture_node.image = bpy_image
                texture_node.location.x -= 500
                princ_shader = node_tree.nodes['Principled BSDF']
                node_tree.links.new(
                    texture_node.outputs['Color'],
                    princ_shader.inputs['Base Color']
                )
            else:
                bpy_texture.image = bpy_image
                texture_slot = obj.data.materials[0].texture_slots.add()
                texture_slot.texture = bpy_texture
        return objs
