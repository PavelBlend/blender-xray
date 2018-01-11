import bpy

from tests.utils import XRayTestCase
from io_scene_xray.edit_helpers.base import get_object_helper
from io_scene_xray.utils import is_helper_object


class TestBoneEditHelpers(XRayTestCase):
    def test_edit_shape(self):
        op_edit = bpy.ops.io_scene_xray.edit_bone_shape
        bpy.context.scene.objects.active = None
        self.assertFalse(op_edit.poll(), msg='no armature')

        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_armature.object'}],
            shaped_bones=False
        )
        arm = bpy.context.active_object
        bone = arm.data.bones['Bone']
        arm.data.bones.active = bone
        self.assertFalse(op_edit.poll(), msg='an armature, no shape')
        bone.xray.shape.type = '1'
        self.assertTrue(op_edit.poll(), msg='an armature, with shape')
        self.assertIsNone(get_object_helper(bpy.context), msg='no edit helper yet')

        op_edit()
        self.assertIsNotNone(get_object_helper(bpy.context), msg='a box edit helper')
        self.assertFalse(op_edit.poll(), msg='a helper is already active')
        helper = bpy.context.active_object
        self.assertTrue(is_helper_object(helper), msg='active is helper')
        self.assertGreater(helper.scale.length, 0.001, 'a helper with some size')

        bpy.context.scene.objects.active = arm
        self.assertFalse(op_edit.poll(), msg='a helper is still active')
        bpy.context.scene.objects.active = helper

        helper.location = helper.scale = (1, 2, 3)
        bpy.ops.io_scene_xray.edit_bone_shape_fit()
        self.assertLess(helper.location.length, 0.1, msg='fit shape location')
        self.assertLess(helper.scale.length, 0.1, msg='fit shape size')
        self.assertIsNotNone(get_object_helper(bpy.context), msg='a helper still shown')

        bpy.ops.io_scene_xray.edit_bone_shape_apply()
        self.assertIsNone(get_object_helper(bpy.context), msg='a helper is hidden')
        self.assertTrue(_has_nonzero(bone.xray.shape.box_rot), msg='has box_rot')
        self.assertFalse(_has_nonzero(bone.xray.shape.box_trn), msg='has zero box_trn')
        self.assertTrue(_has_nonzero(bone.xray.shape.box_hsz), msg='has box_hsz')

        bone.xray.shape.type = '2'
        op_edit()
        self.assertIsNotNone(get_object_helper(bpy.context), msg='a sphere edit helper')
        helper = bpy.context.active_object
        helper.location = helper.scale = (1, 2, 3)
        bpy.ops.io_scene_xray.edit_bone_shape_fit()
        self.assertLess(helper.location.length, 0.1, msg='fit shape sphere location')
        bpy.ops.io_scene_xray.edit_bone_shape_apply()
        self.assertGreater(bone.xray.shape.sph_rad, 0.01, msg='has sph_rad')

        op_edit()
        bone.xray.shape.type = '3'
        self.assertIsNotNone(get_object_helper(bpy.context), msg='a cylinder edit helper')
        helper = bpy.context.active_object
        helper.location = helper.scale = (1, 2, 3)
        bpy.ops.io_scene_xray.edit_bone_shape_fit()
        self.assertLess(helper.location.length, 0.1, msg='fit shape cylinder location')
        bpy.ops.io_scene_xray.edit_bone_shape_apply()
        bpy.context.scene.update()
        self.assertGreater(bone.xray.shape.cyl_hgh, 0.01, msg='has cyl_hgh')

        op_edit()
        self.assertIsNotNone(get_object_helper(bpy.context), msg='anedit helper again')
        bpy.ops.io_scene_xray.edit_cancel()
        self.assertIsNone(get_object_helper(bpy.context), msg='no edit helper again')

        op_edit()
        self.assertIsNotNone(get_object_helper(bpy.context), msg='an edit helper once again')
        bone.xray.shape.type = '0'
        self.assertIsNone(get_object_helper(bpy.context), msg='no edit helper once again')

    def test_edit_center(self):
        op_edit = bpy.ops.io_scene_xray.edit_bone_center
        bpy.context.scene.objects.active = None
        self.assertFalse(op_edit.poll(), msg='no armature')

        bpy.ops.xray_import.object(
            directory=self.relpath(),
            files=[{'name': 'test_fmt_armature.object'}],
            shaped_bones=False
        )
        arm = bpy.context.active_object
        bone = arm.data.bones['Bone1']
        arm.data.bones.active = bone
        self.assertTrue(op_edit.poll(), msg='an armature')
        self.assertIsNone(get_object_helper(bpy.context), msg='no edit helper yet')

        op_edit()
        self.assertIsNotNone(get_object_helper(bpy.context), msg='an edit helper')
        self.assertFalse(op_edit.poll(), msg='a helper is already active')
        helper = bpy.context.active_object
        self.assertTrue(is_helper_object(helper), msg='active is helper')
        self.assertGreater(helper.location.length, 0.001, 'a helper with some location')

        bpy.context.scene.objects.active = arm
        self.assertFalse(op_edit.poll(), msg='a helper is still active')
        bpy.context.scene.objects.active = helper

        helper.location = (0, 0, 0)
        bpy.ops.io_scene_xray.edit_bone_center_apply()
        self.assertIsNone(get_object_helper(bpy.context), msg='a helper is hidden')
        self.assertTrue(_has_nonzero(bone.xray.mass.center), msg='has center relative')


def _has_nonzero(vec):
    for val in vec:
        if val:
            return True
    return False
