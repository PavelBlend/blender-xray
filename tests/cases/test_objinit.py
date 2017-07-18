from tests import utils

import bpy
from io_scene_xray import plugin, utils as utl


class TestObjectInitialize(utils.XRayTestCase):
    def test_import_version_and_root(self):
        # Arrange
        version = utl.plugin_version_number()

        # Act
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.object'}],
        )
        plugin.scene_update_post(bpy.context.scene)

        # Assert
        obj = bpy.data.objects['Plane']
        self.assertEqual(obj.type, 'MESH')
        self.assertEqual(obj.xray.version, version)
        self.assertEqual(obj.xray.root, True)

    def test_init_version(self):
        # Arrange
        obj = bpy.data.objects.new('obj', None)

        # Act
        plugin.scene_update_post(bpy.context.scene)

        # Assert
        self.assertNotEqual(obj.xray.version, 0)

    def test_init_root(self):
        # Arrange
        obj_mesh = bpy.data.objects.new('mesh', bpy.data.meshes.new('mesh'))
        obj_arma = bpy.data.objects.new('arma', bpy.data.armatures.new('arma'))
        obj_lamp = bpy.data.objects.new('lamp', bpy.data.lamps.new('lamp', 'POINT'))

        # Act
        plugin.scene_update_post(bpy.context.scene)

        # Assert
        self.assertEqual(obj_mesh.xray.root, True)
        self.assertEqual(obj_arma.xray.root, False)
        self.assertEqual(obj_lamp.xray.root, False)
