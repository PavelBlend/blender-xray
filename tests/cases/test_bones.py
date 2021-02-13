from tests import utils

import bpy


class TestBonesImport(utils.XRayTestCase):
    def test_default(self):
        # import mesh and armature
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_bones.object'}],
        )
        arm_obj = bpy.data.objects['test_fmt_bones.object']
        utils.set_active_object(arm_obj)

        # remove "bone or parts" (bone groups)
        for bone_group in arm_obj.pose.bone_groups:
            arm_obj.pose.bone_groups.remove(bone_group)

        # Act import
        bpy.ops.xray_import.bones(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.bones'}],
            import_bone_parts=True,
            import_bone_properties=True
        )

        # Assert
        self.assertReportsNotContains('WARNING')

        # Act export
        bpy.ops.xray_export.bones(
            directory=self.relpath(),
            filepath=self.outpath('test.bones'),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )

        # test blender ik limits
        arm_obj.data.xray.joint_limits_type = 'IK'
        bpy.ops.xray_export.bones(
            directory=self.relpath(),
            filepath=self.outpath('test_blender_ik.bones'),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )

        # test export null boneparts
        # remove "bone or parts" (bone groups)
        for bone_group in arm_obj.pose.bone_groups:
            arm_obj.pose.bone_groups.remove(bone_group)

        # Act export
        bpy.ops.xray_export.bones(
            directory=self.relpath(),
            filepath=self.outpath('test_nul_boneparts.bones'),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )

        # Assert
        self.assertOutputFiles({
            'test.bones', 'test_blender_ik.bones', 'test_nul_boneparts.bones'
        })
