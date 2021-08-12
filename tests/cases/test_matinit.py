from tests import utils

import bpy
from io_scene_xray import plugins, utils as utl


class TestMaterialInitialize(utils.XRayTestCase):
    def test_import_version_and_shaders(self):
        # Arrange
        version = utl.plugin_version_number()

        # Act
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.object'}],
        )
        plugins.scene_update_post(bpy.context.scene)

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
        utils.link_object(obj)
        utils.set_active_object(obj)

        mat = bpy.data.materials.new('')

        # Act
        plugins.scene_update_post(bpy.context.scene)

        # Assert
        self.assertEqual(mat.xray.version, version)
        self.assertEqual(mat.xray.eshader, 'default')

    def test_init_shaders_dynamic(self):
        # Arrange
        version = utl.plugin_version_number()

        obj = bpy.data.objects.new('', None)
        obj.xray.flags_custom_type = 'dy'
        utils.link_object(obj)
        utils.set_active_object(obj)

        mat = bpy.data.materials.new('')

        # Act
        plugins.scene_update_post(bpy.context.scene)

        # Assert
        self.assertEqual(mat.xray.version, version)
        self.assertEqual(mat.xray.eshader, 'models\\model')
