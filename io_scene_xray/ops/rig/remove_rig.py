# blender modules
import bpy

# addon modules
from ... import utils
from ... import text


def change_bone_parents(arm_obj):
    bpy.ops.object.mode_set(mode='EDIT')

    try:
        for bone in arm_obj.data.bones:
            parent = utils.bone.find_bone_exportable_parent(bone)

            edit_bone = arm_obj.data.edit_bones[bone.name]
            if parent:
                edit_parent = arm_obj.data.edit_bones[parent.name]
            else:
                edit_parent = None

            edit_bone.parent = edit_parent

    finally:
        bpy.ops.object.mode_set(mode='OBJECT')


def remove_bone_constraints(arm_obj):
    bpy.ops.object.mode_set(mode='POSE')

    try:
        for pose_bone in arm_obj.pose.bones:
            for constraint in pose_bone.constraints:
                pose_bone.constraints.remove(constraint)

    finally:
        bpy.ops.object.mode_set(mode='OBJECT')


def remove_non_exportable_bones(arm_obj):
    bpy.ops.object.mode_set(mode='EDIT')

    try:
        for edit_bone in arm_obj.data.edit_bones:
            bone = arm_obj.data.bones[edit_bone.name]

            if not utils.bone.is_exportable_bone(bone):
                arm_obj.data.edit_bones.remove(edit_bone)

    finally:
        bpy.ops.object.mode_set(mode='OBJECT')


def move_bones_on_first_layer(arm_obj):
    layers = [False, ] * 32
    layers[0] = True

    for bone in arm_obj.data.bones:
        bone.layers = layers


class XRAY_OT_remove_rig(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.remove_rig'
    bl_label = 'Remove Rig'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active and active.type == 'ARMATURE'

    def draw(self, context):    # pragma: no cover
        self.layout.label(
            text=text.get_tip(text.warn.remove_rig_warn),
            icon='ERROR'
        )

    @utils.set_cursor_state
    def execute(self, context):
        arm_obj = context.active_object

        change_bone_parents(arm_obj)
        remove_bone_constraints(arm_obj)
        remove_non_exportable_bones(arm_obj)
        move_bones_on_first_layer(arm_obj)

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        return context.window_manager.invoke_props_dialog(self, width=700)


def register():
    bpy.utils.register_class(XRAY_OT_remove_rig)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_remove_rig)
