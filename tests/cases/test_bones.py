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

        NAME_TEST = 'test.bones'
        NAME_IK_LIMITS = 'ik_limits.bones'
        NAME_NULL_BONEPARTS = 'null_boneparts.bones'
        NAME_BATCH_EXPORT = 'batch_export.bones'

        # Act export
        arm_obj.name = NAME_TEST
        bpy.ops.xray_export.bones(
            filepath=self.outpath(NAME_TEST),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )

        # test blender ik limits
        arm_obj.name = NAME_IK_LIMITS
        arm_obj.data.xray.joint_limits_type = 'IK'
        bpy.ops.xray_export.bones(
            filepath=self.outpath(NAME_IK_LIMITS),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )

        # test export null boneparts
        # remove "bone or parts" (bone groups)
        for bone_group in arm_obj.pose.bone_groups:
            arm_obj.pose.bone_groups.remove(bone_group)

        # Act export
        arm_obj.name = NAME_NULL_BONEPARTS
        bpy.ops.xray_export.bones(
            filepath=self.outpath(NAME_NULL_BONEPARTS),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )

        # Batch export test
        arm_obj.name = NAME_BATCH_EXPORT
        bpy.ops.xray_export.bones_batch(
            directory=self.outpath(),
            objects=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )

        # Assert
        self.assertOutputFiles({
            NAME_TEST,
            NAME_IK_LIMITS,
            NAME_NULL_BONEPARTS,
            NAME_BATCH_EXPORT
        })
