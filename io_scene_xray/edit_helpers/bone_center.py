import bpy
import mathutils

from io_scene_xray import registry
from io_scene_xray.xray_motions import MATRIX_BONE, MATRIX_BONE_INVERTED
from .base_bone import AbstractBoneEditHelper


class _BoneCenterEditHelper(AbstractBoneEditHelper):
    def draw(self, layout, context):
        if self.is_active(context):
            layout.operator(_CenterEditApplyOp.bl_idname, icon='FILE_TICK')
            super().draw(layout, context)
            return

        lay = layout
        if context.active_bone.xray.shape.type == '0':
            lay = lay.split(align=True)
            lay.enabled = False
        lay.operator(EditCenter.bl_idname, text='Edit Center')

    def _create_helper(self, name):
        helper = bpy.data.objects.new(name, None)
        helper.empty_draw_size = 0.05
        helper.lock_rotation = helper.lock_scale = (True, True, True)
        return helper

    def _update_helper(self, helper, target):
        super()._update_helper(helper, target)
        bone = target

        mat = bone.matrix_local * MATRIX_BONE_INVERTED
        mat *= mathutils.Matrix.Translation(bone.xray.mass.center)
        helper.location = mat.to_translation()


HELPER = _BoneCenterEditHelper('bone-center-edit')


@registry.module_thing
class EditCenter(bpy.types.Operator):
    bl_idname = 'io_scene_xray.edit_bone_center'
    bl_label = 'Edit Bone Center'
    bl_description = 'Create a helper object that can be used for adjusting bone center'

    @classmethod
    def poll(cls, context):
        return context.active_bone and not HELPER.is_active(context)

    def execute(self, context):
        target = context.active_object.data.bones[context.active_bone.name]
        HELPER.activate(target)
        return {'FINISHED'}


@registry.module_thing
class _CenterEditApplyOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.edit_bone_center_apply'
    bl_label = 'Apply Center'
    bl_options = {'UNDO'}

    def execute(self, _context):
        helper, bone = HELPER.get_target()
        mat = MATRIX_BONE * bone.matrix_local.inverted() * helper.matrix_local
        bone.xray.mass.center = mat.to_translation()
        HELPER.deactivate()
        bpy.context.scene.update()
        return {'FINISHED'}
