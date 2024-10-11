import bpy
import tests
import io_scene_xray


class TestOmf(tests.utils.XRayTestCase):
    def test_general(self):
        # import mesh and armature
        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_omf.object'}],
        )
        arm_obj = bpy.data.objects['test_fmt_omf.object']
        tests.utils.set_active_object(arm_obj)

        # import motions
        bpy.ops.xray_import.omf(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.omf'}],
            import_motions=True,
            import_bone_parts=True,
            add_to_motion_list=True
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
        tests.utils.select_object(arm_obj)
        tests.utils.set_active_object(arm_obj)

        # import motions
        bpy.ops.xray_import.omf(
            directory=self.binpath(),
            files=[{'name': 'test_fmt.omf'}],
            import_motions=True,
            import_bone_parts=True,
            add_to_motion_list=True
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
        tests.utils.link_object(new_arm_obj)
        tests.utils.select_object(new_arm_obj)

        # batch export
        bpy.ops.xray_export.omf(directory=self.outpath())
        self.assertOutputFiles({'test_omf_1.omf', 'test_omf_2.omf'})

    def test_merge_omf(self):
        # create armature and object
        arm = bpy.data.armatures.new('arm')
        obj = bpy.data.objects.new('test_obj', arm)

        tests.utils.link_object(obj)
        tests.utils.set_active_object(obj)

        ver = io_scene_xray.utils.addon_version_number()
        obj.xray.version = ver
        obj.xray.isroot = True

        # create bones
        bpy.ops.object.mode_set(mode='EDIT')
        for bone_index in range(2):
            bone = arm.edit_bones.new('bone_{}'.format(bone_index))
            bone.head = (0, 0, bone_index)
            bone.tail = (0, 1, bone_index)

        arm.edit_bones[1].parent = arm.edit_bones[0]
        bpy.ops.object.mode_set(mode='OBJECT')

        # create actions
        anim_data = obj.animation_data_create()

        bpy.ops.object.mode_set(mode='POSE')
        bone_group = obj.pose.bone_groups.new(name='default')
        for bone in obj.pose.bones:
            bone.rotation_mode = 'ZXY'
            bone.bone_group = bone_group
        bpy.ops.object.mode_set(mode='OBJECT')

        acts = []

        for act_index in range(3):
            act_name = 'act_{}'.format(act_index)
            act = bpy.data.actions.new(act_name)
            acts.append(act)

            for bone_name in ('bone_0', 'bone_1'):

                for curve_index in range(3):
                    fcurve_loc = act.fcurves.new(
                        'pose.bones["{}"].location'.format(bone_name),
                        index=curve_index
                    )
                    fcurve_rot = act.fcurves.new(
                        'pose.bones["{}"].rotation_euler'.format(bone_name),
                        index=curve_index
                    )

                    for frame, value in zip((0, 10), (0, 1)):
                        key = fcurve_loc.keyframe_points.insert(frame, value)
                        key.interpolation = 'BEZIER'

                        key = fcurve_rot.keyframe_points.insert(frame, value)
                        key.interpolation = 'BEZIER'

        # export
        for i in (0, 1):
            act = acts[i]
            motion = obj.xray.motions_collection.add()
            motion.name = act.name

        bpy.ops.xray_export.omf_file(
            filepath=self.outpath('test_1.omf'),
            export_mode='OVERWRITE',
            export_motions=True,
            export_bone_parts=True
        )

        obj.xray.motions_collection.clear()
        act = acts[2]
        motion = obj.xray.motions_collection.add()
        motion.name = act.name

        bpy.ops.xray_export.omf_file(
            filepath=self.outpath('test_2.omf'),
            export_mode='OVERWRITE',
            export_motions=True,
            export_bone_parts=True
        )

        # select
        bpy.ops.io_scene_xray.add_omf(
            directory=self.outpath(),
            files=(
                {'name': 'test_1.omf'},
                {'name': 'test_2.omf'}
            ),
        )

        # merge
        bpy.ops.io_scene_xray.merge_omf(
            directory=self.outpath(),
            filepath='merged.omf'
        )

        # import merged
        bpy.ops.xray_import.omf(
            directory=self.outpath(),
            files=[{'name': 'merged.omf'}],
            import_motions=True,
            import_bone_parts=True,
            add_to_motion_list=True
        )

        self.assertOutputFiles({'test_1.omf', 'test_2.omf', 'merged.omf'})
        self.assertReportsNotContains()
