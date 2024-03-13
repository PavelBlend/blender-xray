import re
import bpy
import tests


class TestDmExport(tests.utils.XRayTestCase):
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

    def test_export_batch(self):
        # Arrange
        self._create_dm_objects()

        # select objects
        names = set()
        for obj in bpy.data.objects:
            tests.utils.select_object(obj)
            names.add(obj.name)

        # Act
        bpy.ops.xray_export.dm(
            detail_models=','.join(names),
            directory=self.outpath(),
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({'tdm1.dm', 'tdm2.dm', 'tdm3.dm'})

    def test_error_many_uv(self):
        # Arrange
        objs = self._create_dm_objects()
        obj = objs[0]

        uv_layer = obj.data.uv_layers.new(name='test')

        # Act
        bpy.ops.xray_export.dm_file(
            detail_model=obj.name,
            filepath=self.outpath('test_error.dm'),
            texture_name_from_image_path=False
        )

        obj.data.uv_layers.remove(uv_layer)

        # Assert
        self.assertReportsNotContains('ERROR')
        self.assertReportsContains(
            'WARNING',
            re.compile('Object has more than one UV-map. Active UV-map exported')
        )

    def test_error_no_uv(self):
        # Arrange
        objs = self._create_dm_objects()
        obj = objs[0]

        uv_layer = obj.data.uv_layers[0]
        obj.data.uv_layers.remove(uv_layer)

        # Act
        bpy.ops.xray_export.dm_file(
            detail_model=obj.name,
            filepath=self.outpath('test_error.dm'),
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Mesh-object has no UV-map')
        )

    def test_error_many_materials(self):
        # Arrange
        objs = self._create_dm_objects()
        obj = objs[0]

        mat = bpy.data.materials.new('test')
        obj.data.materials.append(mat)

        # Act
        bpy.ops.xray_export.dm_file(
            detail_model=obj.name,
            filepath=self.outpath('test_error.dm'),
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Mesh-object has more than one material')
        )

    def test_error_no_materials(self):
        # Arrange
        objs = self._create_dm_objects()
        obj = objs[0]

        obj.data.materials.clear()

        # Act
        bpy.ops.xray_export.dm_file(
            detail_model=obj.name,
            filepath=self.outpath('test_error.dm'),
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Object has no material')
        )

    def test_error_empty_material_slot(self):
        # Arrange
        objs = self._create_dm_objects()
        obj = objs[0]

        obj.data.materials.clear()
        tests.utils.set_active_object(obj)
        bpy.ops.object.material_slot_add()

        # Act
        bpy.ops.xray_export.dm_file(
            detail_model=obj.name,
            filepath=self.outpath('test_error.dm'),
            texture_name_from_image_path=False
        )

        # Assert
        self.assertReportsContains(
            'ERROR',
            re.compile('Object use empty material slot')
        )

    def _create_dm_objects(self, create_uv=True, create_material=True):
        bmesh = tests.utils.create_bmesh(
            # verts
            ((0, 0, 0), (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0)),
            # faces
            ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)),
            create_uv
        )

        objs = []

        for i in range(3):
            obj = tests.utils.create_object(bmesh, create_material)
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
