# blender modules
import bpy
import mathutils

# addon modules
from . import base_bone
from ... import formats
from ... import text
from ... import utils


def get_mass_matrix(bone):
    global pose_bone
    pose_bone = bpy.context.active_object.pose.bones[bone.name]
    mat = utils.version.multiply(
        pose_bone.matrix,
        formats.motions.const.MATRIX_BONE_INVERTED
    )
    mat = utils.version.multiply(
        mat,
        mathutils.Matrix.Translation(bone.xray.mass.center)
    )
    return mat


def apply_mass_matrix(bone, mass_mat):
    global pose_bone
    mat = utils.version.multiply(
        formats.motions.const.MATRIX_BONE,
        pose_bone.matrix.inverted(),
        mass_mat
    )
    bone.xray.mass.center = mat.to_translation()


class _BoneCenterEditHelper(base_bone.AbstractBoneEditHelper):
    size = 0.5

    def draw(self, layout, context):    # pragma: no cover
        if self.is_active(context):
            layout.operator(
                XRAY_OT_apply_center.bl_idname,
                text=text.get_iface(text.iface.apply_center),
                icon='FILE_TICK'
            )
            layout.operator(
                XRAY_OT_align_center.bl_idname,
                text=text.get_iface(text.iface.align_center),
                icon='CURSOR'
            )
            super().draw(layout, context)
            return

        layout.operator(
            XRAY_OT_edit_center.bl_idname,
            text=text.get_iface(text.iface.edit_center)
        )

    def _create_helper(self, name):
        helper = bpy.data.objects.new(name, None)
        utils.version.set_empty_draw_size(helper, self.size)
        helper.lock_rotation = helper.lock_scale = (True, True, True)
        return helper

    def _update_helper(self, helper, target):
        super()._update_helper(helper, target)
        bone = target

        mat = get_mass_matrix(bone)

        helper.location = mat.to_translation()


HELPER = _BoneCenterEditHelper('bone-center-edit')


class XRAY_OT_edit_center(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.edit_bone_center'
    bl_label = 'Edit Bone Center'
    bl_description = 'Create a helper object that can be ' \
        'used for adjusting bone center'

    @classmethod
    def poll(cls, context):
        return context.active_bone and not HELPER.is_active(context)

    def execute(self, context):
        target = context.active_object.data.bones[context.active_bone.name]
        HELPER.activate(target)
        return {'FINISHED'}


class XRAY_OT_align_center(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.edit_bone_center_align'
    bl_label = text.iface.align_center

    @classmethod
    def poll(cls, context):
        _, bone = HELPER.get_target()
        if not bone:
            return
        return bone.xray.shape.type not in ('0', '4')

    def execute(self, context):
        helper, bone = HELPER.get_target()
        shape = bone.xray.shape
        mat = utils.version.multiply(
            pose_bone.matrix,
            formats.motions.const.MATRIX_BONE_INVERTED
        )
        pos = None
        if shape.type == '1':
            pos = shape.box_trn
        elif shape.type == '2':
            pos = shape.sph_pos
        elif shape.type == '3':
            pos = shape.cyl_pos
        mat = utils.version.multiply(
            mat, mathutils.Matrix.Translation((pos[0], pos[2], pos[1]))
        )
        helper.location = mat.to_translation()
        return {'FINISHED'}


class XRAY_OT_apply_center(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.edit_bone_center_apply'
    bl_label = text.iface.apply_center
    bl_options = {'UNDO'}

    def execute(self, context):
        helper, bone = HELPER.get_target()
        apply_mass_matrix(bone, helper.matrix_local)
        HELPER.deactivate()
        if utils.version.IS_28:
            bpy.context.view_layer.update()
        else:
            bpy.context.scene.update()
        return {'FINISHED'}


classes = (
    XRAY_OT_edit_center,
    XRAY_OT_align_center,
    XRAY_OT_apply_center
)


def register():
    for operator in classes:
        bpy.utils.register_class(operator)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
