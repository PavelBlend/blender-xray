from tests import utils

import bpy


class TestArmature(utils.XRayTestCase):
    def test_armature(self):
        # Arrange
        arm = bpy.data.armatures.new('test')
        obj = bpy.data.objects.new('test', arm)
        utils.link_object(obj)
        utils.set_active_object(obj)
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bone = arm.edit_bones.new('non-exp')
            bone.head.z = 0.5
            bone = arm.edit_bones.new('exp')
            bone.head.z = 0.5
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        arm.bones['non-exp'].xray.exportable = False

        bmesh = utils.create_bmesh((
            (0, 0, 0),
            (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0),
        ), ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)), True)
        obj_me = utils.create_object(bmesh, True)
        obj_me.parent = obj
        obj_me.xray.isroot = False
        group = obj_me.vertex_groups.new(name='exp')
        group.add(range(len(obj_me.data.vertices)), 1, 'REPLACE')

        # Act
        bpy.ops.xray_export.object(
            objects=obj.name, directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False,
        )

        # Assert
        bpy.ops.xray_import.object(
            directory=self.outpath(),
            files=[{'name': 'test.object'}],
        )

        obj_arm = bpy.data.objects['test.object']
        self.assertEqual(obj_arm.type, 'ARMATURE')
        self.assertEqual(obj_arm.xray.isroot, True)

        imp_arm = bpy.data.armatures[1]
        self.assertEqual(len(imp_arm.bones), 1)
