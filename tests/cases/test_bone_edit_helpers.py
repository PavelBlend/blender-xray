import bpy

from tests.utils import XRayTestCase, set_active_object
from io_scene_xray.ops.edit_helpers.base import get_object_helper
from io_scene_xray.utils.obj import is_helper_object


class TestBoneEditHelpers(XRayTestCase):
    def test_edit_shape(self):
        op_edit = bpy.ops.io_scene_xray.edit_bone_shape
        if bpy.app.version >= (2, 80, 0):
            bpy.context.view_layer.objects.active = None
        else:
            bpy.context.scene.objects.active = None
        self.assertFalse(op_edit.poll(), msg='no armature')

        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_armature.object'}]
        )
        msh = bpy.data.objects['Plane']
        msh.location.z += 0.1
        msh.scale *= 0.75
        arm = bpy.data.objects['test_fmt_armature.object']
        arm.scale *= 2
        set_active_object(arm)
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

        set_active_object(arm)
        self.assertFalse(op_edit.poll(), msg='a helper is still active')
        set_active_object(helper)

        helper.location = helper.scale = (1, 2, 3)
        bpy.ops.io_scene_xray.edit_bone_shape_fit()
        self.assertAlmostEqualV(helper.location, (0, 0, 0.1), 1e-3, msg='fit shape location')
        self.assertAlmostEqualV(helper.scale, (0.022, 0.022, 0.008), 1e-3, msg='fit shape size')
        self.assertIsNotNone(get_object_helper(bpy.context), msg='a helper still shown')

        bpy.ops.io_scene_xray.edit_bone_shape_apply()
        self.assertIsNone(get_object_helper(bpy.context), msg='a helper is hidden')
        self.assertAlmostEqualV(bone.xray.shape.box_rot, (+1,0,0, 0,0,+1, 0,-1,0), 0.02, msg='has box_rot')
        self.assertAlmostEqualV(bone.xray.shape.box_trn, (0, 0.1, 0), 1e-3, msg='has box_trn')
        self.assertAlmostEqualV(bone.xray.shape.box_hsz, (0.022, 0.022, 0.008), 1e-3, msg='has box_hsz')
        scale = bone.xray.shape.get_matrix_basis().to_scale()
        self.assertAlmostEqualV(scale, (1, 1, 1), 1e-3, msg='close to 1:1 scale')
        self.assertLess(reapply_max_difference(bone.xray.shape), 0.1, msg='box reapplies almost the same')

        bone.xray.shape.type = '2'
        op_edit()
        self.assertIsNotNone(get_object_helper(bpy.context), msg='a sphere edit helper')
        helper = bpy.context.active_object
        helper.location = helper.scale = (1, 2, 3)
        bpy.ops.io_scene_xray.edit_bone_shape_fit()
        self.assertAlmostEqualV(helper.location, (0, 0, 0.1), 1e-3, msg='fit shape sphere location')
        bpy.ops.io_scene_xray.edit_bone_shape_apply()
        self.assertAlmostEqual(bone.xray.shape.sph_rad, 0.073, delta=1e-3, msg='has sph_rad')
        self.assertLess(reapply_max_difference(bone.xray.shape), 0.1, msg='sphere reapplies almost the same')

        bone.xray.shape.type = '3'
        op_edit()
        self.assertIsNotNone(get_object_helper(bpy.context), msg='a cylinder edit helper')
        helper = bpy.context.active_object
        helper.location = helper.scale = (1, 2, 3)
        bpy.ops.io_scene_xray.edit_bone_shape_fit()
        self.assertAlmostEqualV(helper.location, (0, 0, 0.1), 1e-3, msg='fit shape cylinder location')
        bpy.ops.io_scene_xray.edit_bone_shape_apply()
        self.assertAlmostEqual(bone.xray.shape.cyl_hgh, 0.016, delta=1e-3, msg='has cyl_hgh')
        self.assertLess(reapply_max_difference(bone.xray.shape), 0.1, msg='cylinder reapplies almost the same')

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
        set_active_object(None)
        self.assertFalse(op_edit.poll(), msg='no armature')

        bpy.ops.xray_import.object(
            directory=self.binpath(),
            files=[{'name': 'test_fmt_armature.object'}]
        )
        arm = bpy.data.objects['test_fmt_armature.object']
        set_active_object(arm)
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

        set_active_object(arm)
        self.assertFalse(op_edit.poll(), msg='a helper is still active')
        set_active_object(helper)

        helper.location = (0, 0, 0)
        self.assertFalse(bpy.ops.io_scene_xray.edit_bone_center_align.poll(), msg='no shape')

        bone.xray.shape.type = '1'
        bpy.ops.io_scene_xray.edit_bone_center_align()
        self.assertEqual(round_vec(helper.location, 6), (0.1, 0, 0), msg='move helper to box')

        bone.xray.shape.type = '2'
        bpy.ops.io_scene_xray.edit_bone_center_align()
        self.assertEqual(round_vec(helper.location, 6), (0, 0.2, 0), msg='move helper to sphere')

        bone.xray.shape.type = '3'
        bpy.ops.io_scene_xray.edit_bone_center_align()
        self.assertEqual(round_vec(helper.location, 6), (0, 0, 0.3), msg='move helper to cylinder')

        bpy.ops.io_scene_xray.edit_bone_center_apply()
        self.assertIsNone(get_object_helper(bpy.context), msg='a helper is hidden')
        self.assertTrue(_has_nonzero(bone.xray.mass.center), msg='has center relative')


def _has_nonzero(vec):
    for val in vec:
        if val:
            return True
    return False


def round_vec(vec, ndigits):
    return tuple((round(val, ndigits) for val in vec))


def reapply_max_difference(shape):
    def shape_to_plain(sh):
        return [
            *sh.box_rot, *sh.box_trn, *sh.box_hsz,
            *sh.sph_pos, sh.sph_rad,
            *sh.cyl_dir, sh.cyl_hgh, sh.cyl_rad,
        ]

    old = shape_to_plain(shape)
    bpy.ops.io_scene_xray.edit_bone_shape()
    bpy.ops.io_scene_xray.edit_bone_shape_apply()
    new = shape_to_plain(shape)
    result = 0
    for o, n in zip(old, new):
        result = max(result, abs(o - n))
    return result
