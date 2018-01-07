import bpy

from io_scene_xray import registry, utils

@registry.module_thing
class CreateFakeBones(bpy.types.Operator):
    bl_idname = 'io_scene_xray.create_fake_bones'
    bl_label = 'Create Fake Bones'
    bl_description = 'Connect non-rigid bone joints via fake bones to help with IK'

    @classmethod
    def poll(cls, context):
        return _is_armature_context(context)

    def execute(self, context):
        armature_object = context.object
        armature = armature_object.data
        fake_names = []
        with utils.using_mode('EDIT'):
            for bone in armature.edit_bones:
                parent = bone.parent
                if parent is None:
                    continue
                if bone.head == parent.tail:
                    continue
                if armature.bones[bone.name].xray.ikjoint.is_rigid:
                    continue

                fake_bone = armature.edit_bones.new(name=utils.build_fake_bone_name(bone.name))
                fake_bone.use_deform = False
                fake_bone.hide = True
                fake_bone.parent = parent
                fake_bone.use_connect = True
                fake_bone.tail = bone.head
                bone.parent = fake_bone
                bone.use_connect = True
                fake_names.append(fake_bone.name)

        with utils.using_mode('OBJECT'):
            for name in fake_names:
                pbone = armature_object.pose.bones[name]
                pbone.lock_ik_x = pbone.lock_ik_y = pbone.lock_ik_z = True
                pbone.custom_shape = _get_fake_bone_shape()

                bone = armature.bones[name]
                bone.hide = True

        return {'FINISHED'}


@registry.module_thing
class DeleteFakeBones(bpy.types.Operator):
    bl_idname = 'io_scene_xray.delete_fake_bones'
    bl_label = 'Delete Fake Bones'
    bl_description = 'Delete all previously created fake bones'

    @classmethod
    def poll(cls, context):
        return _is_armature_context_with_fake_bones(context)

    def execute(self, context):
        armature = context.object.data
        with utils.using_mode('EDIT'):
            for bone in tuple(armature.edit_bones):
                if not utils.is_fake_bone_name(bone.name):
                    continue
                armature.edit_bones.remove(bone)

        return {'FINISHED'}


@registry.module_thing
class ToggleFakeBonesVisibility(bpy.types.Operator):
    bl_idname = 'io_scene_xray.toggle_fake_bones_visibility'
    bl_label = 'Show/Hide Fake Bones'
    bl_description = 'Show/Hide all fake bones'

    @classmethod
    def poll(cls, context):
        return _is_armature_context_with_fake_bones(context)

    def execute(self, context):
        bones = [
            bone
            for bone in _bones_from_context(context)
            if utils.is_fake_bone_name(bone.name)
        ]
        hide = any((not bone.hide for bone in bones))
        for bone in bones:
            bone.hide = hide

        return {'FINISHED'}


def _bones_from_context(context):
    armature = context.object.data
    if context.object.mode == 'EDIT':
        return armature.edit_bones
    return armature.bones


def _is_armature_context(context):
    obj = context.object
    if not obj:
        return False
    return obj.type == 'ARMATURE'


def _is_armature_context_with_fake_bones(context):
    if not _is_armature_context(context):
        return False
    for bone in _bones_from_context(context):
        if utils.is_fake_bone_name(bone.name):
            return True
    return False


def _get_fake_bone_shape():
    result = bpy.data.objects.get('fake_bone_shape')
    if result is None:
        result = bpy.data.objects.new('fake_bone_shape', None)
        result.empty_draw_size = 0
    return result
