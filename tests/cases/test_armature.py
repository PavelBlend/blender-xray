from tests import utils

import bpy


class TestArmature(utils.XRayTestCase):
    def test_import_sg_maya(self):
        # Arrange
        arm = bpy.data.armatures.new('test')
        obj = bpy.data.objects.new('test', arm)
        bpy.context.scene.objects.link(obj)
        bpy.context.scene.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bone = arm.edit_bones.new('non-exp')
            bone.head.z = 0.5
            bone = arm.edit_bones.new('exp')
            bone.head.z = 0.5
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        arm.bones['non-exp'].xray.exportable = False

        # Act
        bpy.ops.export_object.xray_objects(
            objects=obj.name, directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False,
        )

        # Assert
        bpy.ops.xray_import.object(
            directory=self.outpath(),
            files=[{'name': 'test.object'}],
        )
        imp_arm = bpy.data.armatures[1]
        self.assertEqual(len(imp_arm.bones), 1)
