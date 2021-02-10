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
        bpy.context.view_layer.objects.active = arm_obj

        # Act
        bpy.ops.xray_import.bones(
            directory=self.relpath(),
            files=[{'name': 'test_fmt.bones'}],
        )

        # Assert
        self.assertReportsNotContains('WARNING')
