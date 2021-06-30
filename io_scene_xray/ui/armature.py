# blender modules
import bpy

# addon modules
from .base import XRayPanel, build_label
from .. import registry, plugin_prefs, prefs
from ..ops import fake_bones, joint_limits
from ..version_utils import get_icon, layout_split
from . import collapsible


@registry.module_thing
class XRAY_PT_ArmaturePanel(XRayPanel):
    bl_context = 'data'
    bl_label = build_label('Skeleton')

    @classmethod
    def poll(cls, context):
        preferences = prefs.utils.get_preferences()
        panel_used = (
            # import plugins
            preferences.enable_object_import or
            preferences.enable_skls_import or
            preferences.enable_bones_import or
            preferences.enable_omf_import or
            # export plugins
            preferences.enable_object_export or
            preferences.enable_skls_export or
            preferences.enable_bones_export or
            preferences.enable_omf_export or
            preferences.enable_ogf_export
        )
        return (
            context.active_object and
            context.active_object.type == 'ARMATURE' and
            panel_used
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

        # joint limits
        row, box = collapsible.draw(
            layout,
            'armature:joint_limits',
            'Joint Limits'
        )
        if box:
            split = layout_split(box, 0.5)
            split.label(text='Export Limits from:')
            split.prop(data, 'joint_limits_type', text='')
            box.prop(data, 'display_bone_limits', toggle=True)
            if data.display_bone_limits:
                column = box.column(align=True)
                column.prop(data, 'display_bone_limits_radius')
                row = column.row(align=True)
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

        # fake bones
        row, box = collapsible.draw(
            layout,
            'armature:fake_bones',
            'Fake Bones'
        )
        if box:
            lay = box.column(align=True)
            row = lay.row(align=True)
            row.operator(fake_bones.CreateFakeBones.bl_idname, text='Create', icon='CONSTRAINT_BONE')
            row.operator(fake_bones.DeleteFakeBones.bl_idname, text='Delete', icon='X')
            lay.operator(
                fake_bones.ToggleFakeBonesVisibility.bl_idname,
                text='Show/Hide',
                icon=get_icon('VISIBLE_IPO_ON'),
            )

        # fake bones
        row, box = collapsible.draw(
            layout,
            'armature:link_or_unlink_bones',
            'Link/Unlink Bones'
        )
        if box:
            box.prop_search(data, 'link_to_armature', bpy.data, 'objects', text='')
            column = box.column(align=True)
            column.operator('io_scene_xray.link_bones')
            column.operator('io_scene_xray.unlink_bones')
