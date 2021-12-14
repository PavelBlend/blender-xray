# blender modules
import bpy

# addon modules
from .. import ie_props
from .. import utils


class XRAY_OT_create_fake_bones(ie_props.BaseOperator):
    bl_idname = 'io_scene_xray.create_fake_bones'
    bl_label = 'Create Fake Bones'
    bl_description = 'Connect non-rigid bone joints via fake bones to help with IK'

    @classmethod
    def poll(cls, context):
        return utils.is_armature_context(context)

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

                bone = armature.bones[name]
                bone.hide = True

        self.report({'INFO'}, 'Created %d fake bones' % len(fake_names))
        return {'FINISHED'}


class XRAY_OT_delete_fake_bones(ie_props.BaseOperator):
    bl_idname = 'io_scene_xray.delete_fake_bones'
    bl_label = 'Delete Fake Bones'
    bl_description = 'Delete all previously created fake bones'

    @classmethod
    def poll(cls, context):
        return _is_armature_context_with_fake_bones(context)

    def execute(self, context):
        armature = context.object.data
        original_count = len(armature.bones)
        with utils.using_mode('EDIT'):
            bones = armature.edit_bones
            for bone in tuple(bones):
                if not utils.is_fake_bone_name(bone.name):
                    continue
                bones.remove(bone)

        self.report(
            {'INFO'},
            'Removed %d fake bones' % (original_count - len(armature.bones)),
        )
        return {'FINISHED'}


class XRAY_OT_toggle_fake_bones_visibility(ie_props.BaseOperator):
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


def _is_armature_context_with_fake_bones(context):
    if not utils.is_armature_context(context):
        return False
    for bone in _bones_from_context(context):
        if utils.is_fake_bone_name(bone.name):
            return True
    return False


classes = (
    XRAY_OT_create_fake_bones,
    XRAY_OT_delete_fake_bones,
    XRAY_OT_toggle_fake_bones_visibility
)


def register():
    for operator in classes:
        bpy.utils.register_class(operator)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
