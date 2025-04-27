import re
import os
import bpy
import tests


class TestOpsMotionBrowser(tests.utils.XRayTestCase):

    def test_motion_browser(self):
        # Arrange
        self._create_objects()
        self._create_animations()
        self._export_animations()

        # Act

        # test skls
        self.obj.xray.motions_browser.file_format = 'SKLS'
        bpy.ops.io_scene_xray.browse_motions_file(filepath=os.path.join(self.outpath(), 'test_obj.skls'))

        self.obj.xray.motions_browser.animations_index = 1

        bpy.ops.io_scene_xray.motions_browser_select(mode='NONE')
        bpy.ops.io_scene_xray.motions_browser_select(mode='INVERT')
        bpy.ops.io_scene_xray.motions_browser_select(mode='ALL')

        bpy.ops.io_scene_xray.motions_browser_import(mode='ACTIVE')
        bpy.ops.io_scene_xray.motions_browser_import(mode='SELECTED')
        bpy.ops.io_scene_xray.motions_browser_import(mode='ALL')

        bpy.ops.io_scene_xray.close_motions_file()

        for act in bpy.data.actions:
            bpy.data.actions.remove(act)

        # test omf
        self.obj.xray.motions_browser.file_format = 'OMF'
        bpy.ops.io_scene_xray.browse_motions_file(filepath=os.path.join(self.outpath(), 'test_obj.omf'))

        self.obj.xray.motions_browser.animations_index = 2

        bpy.ops.io_scene_xray.motions_browser_select(mode='NONE')
        bpy.ops.io_scene_xray.motions_browser_select(mode='INVERT')
        bpy.ops.io_scene_xray.motions_browser_select(mode='ALL')

        bpy.ops.io_scene_xray.motions_browser_import(mode='ACTIVE')
        bpy.ops.io_scene_xray.motions_browser_import(mode='SELECTED')
        bpy.ops.io_scene_xray.motions_browser_import(mode='ALL')

        bpy.ops.io_scene_xray.close_motions_file()

        # Assert

    def _create_objects(self):

        # create armature object
        arm = bpy.data.armatures.new('test_arm')
        self.obj = bpy.data.objects.new('test_obj', arm)
        self.obj.xray.isroot = True

        # set selection and active
        bpy.ops.object.select_all(action='DESELECT')
        tests.utils.link_object(self.obj)
        tests.utils.set_active_object(self.obj)
        tests.utils.select_object(self.obj)

        # create bones
        self.bone_name = 'test_bone'
        bpy.ops.object.mode_set(mode='EDIT')
        bone = arm.edit_bones.new(self.bone_name)
        bone.head = (0.0, 0.0, 0.0)
        bone.tail = (0.0, 0.0, 1.0)

        # create bone groups
        bpy.ops.object.mode_set(mode='POSE')
        group = tests.utils.get_bone_groups(self.obj).new(name='default')
        tests.utils.assign_bone_group(self.obj, self.bone_name, group)

    def _create_animations(self):
        # create actions
        bpy.ops.object.mode_set(mode='POSE')
        self.obj.pose.bones[self.bone_name].rotation_mode = 'ZXY'

        for act_index in range(3):
            act = bpy.data.actions.new('test_action_{}'.format(act_index))
            motion = self.obj.xray.motions_collection.add()
            motion.name = act.name

            # create f-curves
            for fcurve_index in range(3):
                trn_curve = act.fcurves.new(
                    'pose.bones["{}"].location'.format(self.bone_name),
                    index=fcurve_index,
                    action_group=self.bone_name
                )
                rot_curve = act.fcurves.new(
                    'pose.bones["{}"].rotation_euler'.format(self.bone_name),
                    index=fcurve_index,
                    action_group=self.bone_name
                )

                # insert keyframes
                for frame in (0, 10):
                    value = frame / 10
                    trn_curve.keyframe_points.insert(frame, value)
                    rot_curve.keyframe_points.insert(frame, value)

    def _export_animations(self):
        bpy.ops.xray_export.skls(directory=self.outpath())
        bpy.ops.xray_export.omf(directory=self.outpath())

        # remove actions
        self.obj.xray.motions_collection.clear()
        for act in bpy.data.actions:
            bpy.data.actions.remove(act)

        # Assert
        self.assertOutputFiles({'test_obj.skls', 'test_obj.omf'})
