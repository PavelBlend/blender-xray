from tests import utils

import bpy
from io_scene_xray import plugin, utils as utl


class TestMaterialInitialize(utils.XRayTestCase):
    def test_import_version_and_shaders(self):
        # Arrange
        version = utl.plugin_version_number()

        # Act
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.object'}],
        )
        plugin.scene_update_post(bpy.context.scene)

        # Assert
        mat = bpy.data.materials[-1]
        self.assertEqual(mat.xray.version, version)
        self.assertEqual(mat.xray.eshader, 'models\\model')
        self.assertEqual(mat.xray.cshader, 'default')
        self.assertEqual(mat.xray.gamemtl, 'default')

    def test_init_version_and_shaders(self):
        # Arrange
        version = utl.plugin_version_number()

        obj = bpy.data.objects.new('', None)
        obj.xray.flags_custom_type = 'st'
        bpy.context.scene.objects.link(obj)
        bpy.context.scene.objects.active = obj

        mat = bpy.data.materials.new('')

        # Act
        plugin.scene_update_post(bpy.context.scene)

        # Assert
        self.assertEqual(mat.xray.version, version)
        self.assertEqual(mat.xray.eshader, 'default')

    def test_init_shaders_dynamic(self):
        # Arrange
        version = utl.plugin_version_number()

        obj = bpy.data.objects.new('', None)
        obj.xray.flags_custom_type = 'dy'
        bpy.context.scene.objects.link(obj)
        bpy.context.scene.objects.active = obj

        mat = bpy.data.materials.new('')

        # Act
        plugin.scene_update_post(bpy.context.scene)

        # Assert
        self.assertEqual(mat.xray.version, version)
        self.assertEqual(mat.xray.eshader, 'models\\model')
