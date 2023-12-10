from tests import utils

import bpy


class TestDetailsImport(utils.XRayTestCase):
    def test_format_version_3(self):
        # Act
        bpy.ops.xray_import.details(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_v3.details'}],
        )

        # Assert
        self.assertReportsNotContains('ERROR')

        obj = bpy.data.objects['test_fmt_v3.details']

        meshes_object_name = 'test_fmt_v3.details meshes'

        slots = obj.xray.detail.slots
        self.assertEqual(slots.meshes_object, meshes_object_name)
        self.assertEqual(slots.slots_base_object, 'test_fmt_v3.details slots base')
        self.assertEqual(slots.slots_top_object, 'test_fmt_v3.details slots top')

        ligthing = slots.ligthing
        self.assertEqual(ligthing.format, 'builds_1569-cop')
        self.assertEqual(ligthing.lights_image, 'details lights.png')
        self.assertEqual(ligthing.hemi_image, 'details hemi.png')
        self.assertEqual(ligthing.shadows_image, 'details shadows.png')

        meshes = slots.meshes
        self.assertEqual(meshes.mesh_0, 'details meshes 0.png')
        self.assertEqual(meshes.mesh_1, 'details meshes 1.png')
        self.assertEqual(meshes.mesh_2, 'details meshes 2.png')
        self.assertEqual(meshes.mesh_3, 'details meshes 3.png')

        for child_object in obj.children:
            if child_object.name == meshes_object_name:
                self.assertEqual(len(child_object.children), 4)
                for mesh_object in child_object.children:
                    mat = mesh_object.active_material
                    if bpy.app.version >= (2, 80, 0):
                        tex_nodes = []
                        for node in mat.node_tree.nodes:
                            if node.type == 'TEX_IMAGE':
                                tex_nodes.append(node)
                        self.assertEqual(len(tex_nodes), 1)
                        tex = tex_nodes[0]
                        image = tex.image
                        if image:
                            self.assertEqual(mat.name, 'build_details')
                    else:
                        tex = mat.active_texture
                        image = tex.image
                        if image:
                            self.assertEqual(mat.name, 'build_details')
                            self.assertEqual(tex.name, 'build_details')

    def test_format_version_2(self):
        # Act
        bpy.ops.xray_import.details(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_v2.details'}],
        )

        # Assert
        self.assertReportsNotContains('ERROR')

        obj = bpy.data.objects['test_fmt_v2.details']

        meshes_object_name = 'test_fmt_v2.details meshes'

        slots = obj.xray.detail.slots
        self.assertEqual(slots.meshes_object, meshes_object_name)
        self.assertEqual(slots.slots_base_object, 'test_fmt_v2.details slots base')
        self.assertEqual(slots.slots_top_object, 'test_fmt_v2.details slots top')

        ligthing = slots.ligthing
        self.assertEqual(ligthing.format, 'builds_1096-1558')
        self.assertEqual(ligthing.lights_image, 'details lighting.png')

        meshes = slots.meshes
        self.assertEqual(meshes.mesh_0, 'details meshes 0.png')
        self.assertEqual(meshes.mesh_1, 'details meshes 1.png')
        self.assertEqual(meshes.mesh_2, 'details meshes 2.png')
        self.assertEqual(meshes.mesh_3, 'details meshes 3.png')

        for child_object in obj.children:
            if child_object.name == meshes_object_name:
                self.assertEqual(len(child_object.children), 3)

    def test_batch_import(self):
        # Act
        bpy.ops.xray_import.details(
            directory=self.binpath(),
            files=[
                {'name': 'test_fmt_v2.details'},
                {'name': 'test_fmt_v3.details'}
            ],
            details_format='builds_1233-1558'
        )
        # pack images
        utils.set_active_object(bpy.data.objects['test_fmt_v2.details'])
        bpy.ops.io_scene_xray.pack_details_images()
        utils.set_active_object(bpy.data.objects['test_fmt_v3.details'])
        bpy.ops.io_scene_xray.pack_details_images()

        # Assert
        self.assertReportsNotContains('ERROR')

    def test_without_slots(self):
        # Act
        bpy.ops.xray_import.details(
            directory=self.binpath(),
            files=[
                {'name': 'test_fmt_v2.details'},
                {'name': 'test_fmt_v3.details'}
            ],
            load_slots=False,
            models_in_row=False
        )

        # Assert
        self.assertReportsNotContains('ERROR')
