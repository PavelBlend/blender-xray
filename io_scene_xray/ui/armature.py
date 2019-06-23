from .base import XRayPanel, build_label
from .. import registry
from ..ops import fake_bones, joint_limits
from ..version_utils import get_icon


@registry.module_thing
class XRAY_PT_ArmaturePanel(XRayPanel):
    bl_context = 'data'
    bl_label = build_label('Skeleton')

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type == 'ARMATURE'
        )

    def draw(self, context):
        layout = self.layout
        data = context.active_object.data.xray
        verdif = data.check_different_version_bones()
        if verdif != 0:
            from ..xray_inject import XRayBoneProperties
            layout.label(
                text='Found bones, edited with '
                + XRayBoneProperties.ShapeProperties.fmt_version_different(verdif)
                + ' version of this plugin',
                icon='ERROR'
            )
        layout.prop(data, 'display_bone_shapes', toggle=True)
        box = layout.box()
        box.label(text='Joint Limits:')
        box.prop(data, 'joint_limits_type')
        box.prop(data, 'display_bone_limits', toggle=True)
        if data.display_bone_limits:
            box.prop(data, 'display_bone_limits_radius')
            row = box.row(align=True)
            row.prop(data, 'display_bone_limit_x', toggle=True)
            row.prop(data, 'display_bone_limit_y', toggle=True)
            row.prop(data, 'display_bone_limit_z', toggle=True)
        col = box.column(align=True)
        col.operator(
            joint_limits.ConvertJointLimitsToConstraints.bl_idname,
            icon='CONSTRAINT_BONE'
        )
        col.operator(
            joint_limits.RemoveJointLimitsConstraints.bl_idname,
            icon='X'
        )
        col.operator(
            joint_limits.ConvertIKLimitsToXRayLimits.bl_idname
        )
        col.operator(
            joint_limits.ConvertXRayLimitsToIKLimits.bl_idname
        )
        col.operator(
            joint_limits.ClearIKLimits.bl_idname
        )

        lay = layout.column(align=True)
        lay.label(text='Fake Bones:')
        row = lay.row(align=True)
        row.operator(fake_bones.CreateFakeBones.bl_idname, text='Create', icon='CONSTRAINT_BONE')
        row.operator(fake_bones.DeleteFakeBones.bl_idname, text='Delete', icon='X')
        lay.operator(
            fake_bones.ToggleFakeBonesVisibility.bl_idname,
            text='Show/Hide',
            icon=get_icon('VISIBLE_IPO_ON'),
        )
