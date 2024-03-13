import re

from tests import utils

import bpy


class TestBonesImport(utils.XRayTestCase):
    def test_default(self):
        # import mesh and armature
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_bones.object'}],
        )
        arm_obj = bpy.data.objects['test_fmt_bones.object']
        utils.set_active_object(arm_obj)

        # remove "bone or parts" (bone groups)
        for bone_group in arm_obj.pose.bone_groups:
            arm_obj.pose.bone_groups.remove(bone_group)

        # Act import
        bpy.ops.xray_import.bones(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.bones'}],
            import_bone_parts=True,
            import_bone_properties=True
        )

        # Assert
        self.assertReportsNotContains('ERROR')

        NAME_TEST = 'test.bones'
        NAME_IK_LIMITS = 'ik_limits.bones'
        NAME_NULL_BONEPARTS = 'null_boneparts.bones'
        NAME_BATCH_EXPORT = 'batch_export.bones'

        # Act export

        # export all
        arm_obj.name = NAME_TEST
        bpy.ops.xray_export.bones_file(
            filepath=self.outpath(NAME_TEST),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )
        # export without bone properties
        bpy.ops.xray_export.bones_file(
            filepath=self.outpath(NAME_TEST),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=False
        )
        # export without bone parts
        bpy.ops.xray_export.bones_file(
            filepath=self.outpath(NAME_TEST),
            object_name=arm_obj.name,
            export_bone_parts=False,
            export_bone_properties=True
        )
        # test non-exportable bone
        arm_obj.data.bones[0].xray.exportable = False
        bpy.ops.xray_export.bones_file(
            filepath=self.outpath(NAME_TEST),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )
        arm_obj.data.bones[0].xray.exportable = True

        # test breakable
        arm_obj.data.bones[0].xray.ikflags_breakable = False
        arm_obj.data.bones[1].xray.ikflags_breakable = True
        bpy.ops.xray_export.bones_file(
            filepath=self.outpath(NAME_TEST),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )

        # test export without exportable bone groups
        for group in arm_obj.pose.bone_groups:
            arm_obj.pose.bone_groups.remove(group)
        arm_obj.pose.bone_groups.new(name='test')
        bpy.ops.xray_export.bones_file(
            filepath=self.outpath(NAME_TEST),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )

        # test blender ik limits
        arm_obj.name = NAME_IK_LIMITS
        arm_obj.data.xray.joint_limits_type = 'IK'
        bpy.ops.xray_export.bones_file(
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
        bpy.ops.xray_export.bones_file(
            filepath=self.outpath(NAME_NULL_BONEPARTS),
            object_name=arm_obj.name,
            export_bone_parts=True,
            export_bone_properties=True
        )

        # Batch export test
        bpy.ops.object.select_all(action='SELECT')
        arm_obj.name = NAME_BATCH_EXPORT
        bpy.ops.xray_export.bones(
            directory=self.outpath(),
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

    def test_import_without_bone_parts(self):
        # import mesh and armature
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_bones.object'}],
        )
        arm_obj = bpy.data.objects['test_fmt_bones.object']
        utils.set_active_object(arm_obj)

        # remove "bone or parts" (bone groups)
        for bone_group in arm_obj.pose.bone_groups:
            arm_obj.pose.bone_groups.remove(bone_group)

        # Act import
        bpy.ops.xray_import.bones(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.bones'}],
            import_bone_parts=False,
            import_bone_properties=True
        )

        # Assert
        self.assertReportsNotContains('ERROR')

    def test_import_without_bone_props(self):
        # import mesh and armature
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_bones.object'}],
        )
        arm_obj = bpy.data.objects['test_fmt_bones.object']
        utils.set_active_object(arm_obj)

        # remove "bone or parts" (bone groups)
        for bone_group in arm_obj.pose.bone_groups:
            arm_obj.pose.bone_groups.remove(bone_group)

        # Act import
        bpy.ops.xray_import.bones(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.bones'}],
            import_bone_parts=True,
            import_bone_properties=False
        )

        # Assert
        self.assertReportsNotContains('ERROR')

    def test_import_replace_bone_groups(self):
        # import mesh and armature
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_bones.object'}],
        )
        arm_obj = bpy.data.objects['test_fmt_bones.object']
        utils.set_active_object(arm_obj)

        # Act import
        bpy.ops.xray_import.bones(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.bones'}],
            import_bone_parts=True,
            import_bone_properties=False
        )

        # Assert
        self.assertReportsNotContains('ERROR')

    def test_import_has_no_bone(self):
        # import mesh and armature
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_bones.object'}],
        )
        arm_obj = bpy.data.objects['test_fmt_bones.object']
        arm_obj.data.bones[0].name = 'test'
        utils.set_active_object(arm_obj)

        # Act import
        bpy.ops.xray_import.bones(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.bones'}],
            import_bone_parts=True,
            import_bone_properties=True
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('Armature object has no bone')
        )
        self.assertReportsContains(
            'WARNING',
            re.compile('Partition contains missing bone')
        )

    def test_import_not_have_bone_parts(self):
        # import mesh and armature
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_bones.object'}],
        )
        arm_obj = bpy.data.objects['test_fmt_bones.object']
        utils.set_active_object(arm_obj)

        # Act import
        bpy.ops.xray_import.bones(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_no_boneparts.bones'}],
            import_bone_parts=True,
            import_bone_properties=True
        )

        # Assert
        self.assertReportsContains(
            'WARNING',
            re.compile('BONES file does not have boneparts')
        )
