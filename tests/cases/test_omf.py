from tests import utils

import bpy


class TestOmf(utils.XRayTestCase):
    def test_general(self):
        # import mesh and armature
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_omf.object'}],
        )
        arm_obj = bpy.data.objects['test_fmt_omf.object']
        utils.set_active_object(arm_obj)

        # import motions
        bpy.ops.xray_import.omf(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.omf'}],
            import_motions=True,
            import_bone_parts=True,
            add_actions_to_motion_list=True
        )

        # export motions
        bpy.ops.xray_export.omf_file(
            filepath=self.outpath('test.omf'),
            export_mode='OVERWRITE',
            export_motions=True,
            export_bone_parts=True
        )
        bpy.ops.xray_export.omf_file(
            filepath=self.outpath('test.omf'),
            export_mode='REPLACE',
            export_motions=True,
            export_bone_parts=True
        )
        bpy.ops.xray_export.omf_file(
            filepath=self.outpath('test.omf'),
            export_mode='ADD',
            export_motions=True,
            export_bone_parts=True
        )

    def test_batch_export(self):
        # import mesh and armature
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_omf.object'}],
        )
        arm_obj = bpy.data.objects['test_fmt_omf.object']
        arm_obj.name = 'test_omf_1'
        utils.select_object(arm_obj)
        utils.set_active_object(arm_obj)

        # import motions
        bpy.ops.xray_import.omf(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.omf'}],
            import_motions=True,
            import_bone_parts=True,
            add_actions_to_motion_list=True
        )

        # create second object
        acts = []
        for motion in arm_obj.xray.motions_collection:
            act = bpy.data.actions[motion.name]
            new_act = act.copy()
            acts.append(new_act)

        arm_obj.xray.motions_collection.clear()
        for act in acts:
            motion = arm_obj.xray.motions_collection.add()
            motion.name = act.name

        new_arm_obj = arm_obj.copy()
        new_arm_obj.name = 'test_omf_2'
        utils.link_object(new_arm_obj)
        utils.select_object(new_arm_obj)

        # batch export
        bpy.ops.xray_export.omf(directory=self.outpath())
        self.assertOutputFiles({'test_omf_1.omf', 'test_omf_2.omf'})
