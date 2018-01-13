import bpy

from .base import AbstractHelper

#pylint: disable=W0223
class AbstractBoneEditHelper(AbstractHelper):
    def _is_active_target(self, target, context):
        if target is None:
            return False
        bone = context.active_bone
        if bone is None:
            return False
        return (bone.name == target.name) and (bone.id_data == target.id_data)

    def _get_target_object(self, helper):
        split = helper.xray.helper_data.split('/')
        if len(split) != 2:
            return
        arm = bpy.data.armatures.get(split[0], None)
        if arm is None:
            return
        bone = arm.bones.get(split[1], None)
        if bone is None:
            return
        return bone

    def _update_helper(self, helper, target):
        bone = target
        helper.xray.helper_data = bone.id_data.name + '/' + bone.name
