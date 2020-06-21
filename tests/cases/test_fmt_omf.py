from tests import utils

import bpy


class TestOmf(utils.XRayTestCase):
    def test_import_general(self):
        # import mesh and armature
        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_omf.object'}],
        )
        arm_obj = bpy.data.objects['test_fmt_omf.object']
        utils.set_active_object(arm_obj)
        # import motions
        bpy.ops.xray_import.omf(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.omf'}],
            import_motions=True,
            import_bone_parts=True,
            add_actions_to_motion_list=True
        )
        # export motions
        bpy.ops.xray_export.omf(
            filepath=self.outpath('test.omf'),
            export_mode='OVERWRITE',
            export_motions=True,
            export_bone_parts=True
        )
        bpy.ops.xray_export.omf(
            filepath=self.outpath('test.omf'),
            export_mode='REPLACE',
            export_motions=True,
            export_bone_parts=True
        )
        bpy.ops.xray_export.omf(
            filepath=self.outpath('test.omf'),
            export_mode='ADD',
            export_motions=True,
            export_bone_parts=True
        )
