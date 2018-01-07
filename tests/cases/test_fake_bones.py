import bpy

from tests import utils
from io_scene_xray.utils import using_mode, is_fake_bone_name


class TestFakeBones(utils.XRayTestCase):
    def test_create(self):
        operator = bpy.ops.io_scene_xray.create_fake_bones
        bpy.context.scene.objects.active = None
        self.assertFalse(operator.poll(), msg='no armature')

        arm = _create_armature('normal')
        self.assertTrue(operator.poll(), msg='an armature')

        operator()
        self.assertEqual(_fake_names(arm.bones), ['child1.fake', 'child2.fake'], msg='created')

        arm = _create_armature('rigid', rigid=True)
        operator()
        self.assertEqual(_fake_names(arm.bones), [], msg='skip rigid')

        arm = _create_armature('connected', connected=True)
        operator()
        self.assertEqual(_fake_names(arm.bones), [], msg='skip connected')

    def test_delete(self):
        operator = bpy.ops.io_scene_xray.delete_fake_bones
        self.assertFalse(operator.poll(), msg='no armature')

        arm = _create_armature('test')
        self.assertFalse(operator.poll(), msg='not created yet')

        bpy.ops.io_scene_xray.create_fake_bones()
        self.assertTrue(operator.poll(), msg='created')

        operator()
        self.assertEqual(_fake_names(arm.bones), [], msg='removed')

        self.assertFalse(operator.poll(), msg='removed')


    def test_show_hide(self):
        operator = bpy.ops.io_scene_xray.toggle_fake_bones_visibility
        self.assertFalse(operator.poll(), msg='no armature')

        arm = _create_armature('test')
        self.assertFalse(operator.poll(), msg='not created yet')

        bpy.ops.io_scene_xray.create_fake_bones()
        self.assertTrue(operator.poll(), msg='created')

        self.assertEqual(_fake_hides(arm.bones), [True, True], msg='hide by default')
        operator()
        self.assertEqual(_fake_hides(arm.bones), [False, False], msg='shown now')
        with using_mode(mode='EDIT'):
            bones = arm.edit_bones
            self.assertEqual(_fake_hides(bones), [True, True], msg='still hidden in edit-mode')
            operator()
            self.assertEqual(_fake_hides(bones), [False, False], msg='shown in edit-mode')
            operator()
            self.assertEqual(_fake_hides(bones), [True, True], msg='hidden in edit-mode')
        self.assertEqual(_fake_hides(arm.bones), [False, False], msg='still shown in object-mode')
        operator()
        self.assertEqual(_fake_hides(arm.bones), [True, True], msg='hide in object-mode')


def _fake_names(bones):
    return [bone.name for bone in bones if is_fake_bone_name(bone.name)]

def _fake_hides(bones):
    return [bone.hide for bone in bones if is_fake_bone_name(bone.name)]

def _create_armature(name, connected=False, rigid=False):
    arm = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new(name, arm)
    bpy.context.scene.objects.link(obj)
    bpy.context.scene.objects.active = obj

    children = []
    with using_mode(mode='EDIT'):
        root = arm.edit_bones.new('root')
        root.tail = (0, 0, 1)

        child1 = arm.edit_bones.new('child1')
        child1.parent = root
        child1.head = root.tail if connected else (1, 0, 0)
        child1.tail = (0, 1, 1)
        children.append(child1.name)

        child2 = arm.edit_bones.new('child2')
        child2.parent = root
        child2.head = root.tail if connected else (1, 0, 0)
        child2.tail = (1, 0, 1)
        children.append(child2.name)

    with using_mode(mode='OBJECT'):
        ikjoint_type = '0' if rigid else '1'
        for child_name in children:
            arm.bones[child_name].xray.ikjoint.type = ikjoint_type

    return obj.data
