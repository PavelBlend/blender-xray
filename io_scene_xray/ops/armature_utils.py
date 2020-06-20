import bpy

from .. import registry


COPY_TRANSFORMS_NAME = 'blender-xray-link'


@registry.module_thing
class ARMATURE_OT_link_bones(bpy.types.Operator):
    bl_idname = 'io_scene_xray.link_bones'
    bl_label = 'Link Bones'
    bl_description = ''

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        if context.object.type == 'ARMATURE':
            return True

    def execute(self, context):
        arm_obj = context.object
        link_arm_name = arm_obj.data.xray.link_to_armature
        link_arm_obj = bpy.data.objects.get(link_arm_name)
        if not link_arm_obj:
            return {'FINISHED'}
        if link_arm_obj.type != 'ARMATURE':
            return {'FINISHED'}
        if arm_obj.name == link_arm_name:
            return {'FINISHED'}
        for link_bone in link_arm_obj.data.bones:
            bone = arm_obj.data.bones.get(link_bone.name)
            if not bone:
                continue
            pose_bone = arm_obj.pose.bones[bone.name]
            constraint = pose_bone.constraints.get(COPY_TRANSFORMS_NAME)
            if not constraint:
                constraint = pose_bone.constraints.new('COPY_TRANSFORMS')
                constraint.name = COPY_TRANSFORMS_NAME
            constraint.target = link_arm_obj
            constraint.subtarget = link_bone.name
        return {'FINISHED'}


@registry.module_thing
class ARMATURE_OT_unlink_bones(bpy.types.Operator):
    bl_idname = 'io_scene_xray.unlink_bones'
    bl_label = 'Unlink Bones'
    bl_description = ''

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        if context.object.type == 'ARMATURE':
            return True

    def execute(self, context):
        arm_obj = context.object
        for bone in arm_obj.data.bones:
            pose_bone = arm_obj.pose.bones[bone.name]
            constraint = pose_bone.constraints.get(COPY_TRANSFORMS_NAME)
            if not constraint:
                continue
            pose_bone.constraints.remove(constraint)
        return {'FINISHED'}
