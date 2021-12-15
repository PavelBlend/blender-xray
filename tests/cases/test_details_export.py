from tests import utils

import bpy


class TestDetailsExport(utils.XRayTestCase):
    def test_export_version_3(self):
        # Arrange
        self._create_details_objects(3)

        # Act
        bpy.ops.xray_export.details(
            filepath=self.outpath('test_v3.details'),
            format_version='builds_1569-cop',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'test_v3.details'
        })

    def test_export_version_2_1096(self):
        # Arrange
        self._create_details_objects(2)

        # Act
        bpy.ops.xray_export.details(
            filepath=self.outpath('test_v2_1096.details'),
            format_version='builds_1096-1230',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'test_v2_1096.details'
        })

    def test_export_version_2_1233(self):
        # Arrange
        self._create_details_objects(2)

        # Act
        bpy.ops.xray_export.details(
            filepath=self.outpath('test_v2_1233.details'),
            format_version='builds_1233-1558',
            texture_name_from_image_path=False
        )

        # Assert
        self.assertOutputFiles({
            'test_v2_1233.details'
        })

    def _create_details_slots_objects(self, data):

        vertices_1 = (
            (112.0000, -6.0000, -7.2000),
            (114.0000, -6.0000, -7.2000),
            (114.0000, -4.0000, -7.2000),
            (112.0000, -4.0000, -7.2000),
            (114.0000, -6.0000, -7.4000),
            (116.0000, -6.0000, -7.4000),
            (116.0000, -4.0000, -7.4000),
            (114.0000, -4.0000, -7.4000),
            (112.0000, -4.0000, -7.2000),
            (114.0000, -4.0000, -7.2000),
            (114.0000, -2.0000, -7.2000),
            (112.0000, -2.0000, -7.2000),
            (114.0000, -4.0000, -7.4000),
            (116.0000, -4.0000, -7.4000),
            (116.0000, -2.0000, -7.4000),
            (114.0000, -2.0000, -7.4000)
        )

        vertices_2 = (
            (112.0000, -6.0000, -7.0500),
            (114.0000, -6.0000, -7.0500),
            (114.0000, -4.0000, -7.0500),
            (112.0000, -4.0000, -7.0500),
            (114.0000, -6.0000, -7.0500),
            (116.0000, -6.0000, -7.0500),
            (116.0000, -4.0000, -7.0500),
            (114.0000, -4.0000, -7.0500),
            (112.0000, -4.0000, -7.0500),
            (114.0000, -4.0000, -7.0500),
            (114.0000, -2.0000, -7.0500),
            (112.0000, -2.0000, -7.0500),
            (114.0000, -4.0000, -7.0500),
            (116.0000, -4.0000, -7.0500),
            (116.0000, -2.0000, -7.0500),
            (114.0000, -2.0000, -7.0500)
        )

        polygons = (
            (0, 1, 2, 3),
            (4, 5, 6, 7),
            (8, 9, 10, 11),
            (12, 13, 14, 15)
        )

        mesh_1 = bpy.data.meshes.new('slots_1')
        mesh_2 = bpy.data.meshes.new('slots_2')
        mesh_1.from_pydata(vertices_1, (), polygons)
        mesh_2.from_pydata(vertices_2, (), polygons)
        object_1 = bpy.data.objects.new('slots_1', mesh_1)
        object_2 = bpy.data.objects.new('slots_2', mesh_2)
        utils.link_object(object_1)
        utils.link_object(object_2)
        data.slots.slots_base_object = object_1.name
        data.slots.slots_top_object = object_2.name

    def _create_details_objects(self, version, create_uv=True, create_material=True):
        bmesh = utils.create_bmesh((
            (0, 0, 0),
            (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0),
        ), ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)), create_uv)

        root_object = bpy.data.objects.new('Details', None)
        bpy.ops.object.select_all(action='DESELECT')
        utils.link_object(root_object)
        if bpy.app.version >= (2, 80, 0):
            root_object.select_set(True)
        else:
            root_object.select = True
        root_object.xray.is_details = True
        data = root_object.xray.detail

        self._create_details_images(data, version)
        self._create_details_slots_objects(data)

        meshes_object = bpy.data.objects.new('DM Meshes', None)
        utils.link_object(meshes_object)
        meshes_object.parent = root_object

        data.slots.meshes_object = meshes_object.name

        objs = []
        for i in range(3):
            obj = utils.create_object(bmesh, create_material)
            obj.name = 'tdm%d' % (i + 1)
            obj.parent = meshes_object
            obj.xray.is_details = True
            obj.xray.detail.model.index = i
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

    def _create_details_images(self, data, version):

        def _create_image(name, width, height, pixel):
            image = bpy.data.images.new(name, width, height)
            for i in range(0, len(image.pixels), 4):
                image.pixels[i] = pixel[0]
                image.pixels[i + 1] = pixel[1]
                image.pixels[i + 2] = pixel[2]
                image.pixels[i + 3] = pixel[3]
            return image

        meshes_images = []
        meshes = data.slots.meshes
        for i in range(4):
            pixel = (1.0, 0.0, 0.0, 0.5)
            image = _create_image('meshes_{}'.format(i), 4, 4, pixel)
            meshes_images.append(image)
        meshes.mesh_0 = meshes_images[0].name
        meshes.mesh_1 = meshes_images[1].name
        meshes.mesh_2 = meshes_images[2].name
        meshes.mesh_3 = meshes_images[3].name

        if version == 3:
            data.slots.ligthing.format = 'builds_1569-cop'

            pixel = (0.5, 0.5, 0.5, 1.0)
            hemi_image = _create_image('hemi', 2, 2, pixel)

            pixel = (0.0, 0.0, 0.0, 1.0)
            light_image = _create_image('light', 2, 2, pixel)

            pixel = (0.5, 0.5, 0.5, 1.0)
            shadows_image = _create_image('shadows', 2, 2, pixel)

            data.slots.ligthing.lights_image = light_image.name
            data.slots.ligthing.hemi_image = hemi_image.name
            data.slots.ligthing.shadows_image = shadows_image.name

        elif version == 2:
            data.slots.ligthing.format = 'builds_1096-1558'

            pixel = (0.5, 0.5, 0.5, 1.0)
            light_image = _create_image('light', 4, 4, pixel)
            data.slots.ligthing.lights_image = light_image.name
