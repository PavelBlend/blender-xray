import bpy
import tests


class TestArmature(tests.utils.XRayTestCase):
    def test_armature(self):
        # Arrange
        arm = bpy.data.armatures.new('test')
        obj = bpy.data.objects.new('test', arm)

        tests.utils.link_object(obj)
        tests.utils.set_active_object(obj)

        bpy.ops.object.mode_set(mode='EDIT')

        try:
            bone = arm.edit_bones.new('non-exp')
            bone.head.z = 0.5

            bone = arm.edit_bones.new('exp')
            bone.head.z = 0.5

        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        arm.bones['non-exp'].xray.exportable = False

        bmesh = tests.utils.create_bmesh(
            ((0, 0, 0), (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0)),
            ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)),
            True
        )

        obj_me = tests.utils.create_object(bmesh, True)
        obj_me.parent = obj
        obj_me.xray.isroot = False
        group = obj_me.vertex_groups.new(name='exp')
        group.add(range(len(obj_me.data.vertices)), 1, 'REPLACE')

        # Act
        bpy.ops.xray_export.object(
            objects=obj.name,
            directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False
        )

        bpy.ops.xray_import.object(
            directory=self.outpath(),
            files=[{'name': 'test.object'}]
        )

        imported_obj = bpy.data.objects['test.object']
        imported_arm = imported_obj.data

        # Assert
        self.assertEqual(imported_obj.type, 'ARMATURE')
        self.assertEqual(imported_obj.xray.isroot, True)
        self.assertEqual(len(imported_arm.bones), 1)
