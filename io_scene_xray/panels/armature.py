# blender modules
import bpy

# addon modules
from .. import ui
from .. import utils
from .. import props
from .. import text


class XRAY_PT_armature(ui.base.XRayPanel):
    bl_context = 'data'
    bl_label = ui.base.build_label('Armature')

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if not obj:
            return

        if obj.type != 'ARMATURE':
            return

        pref = utils.version.get_preferences()

        panel_used = (
            # import formats
            pref.enable_object_import or
            pref.enable_skls_import or
            pref.enable_ogf_import or
            pref.enable_omf_import or
            pref.enable_bones_import or

            # export formats
            pref.enable_object_export or
            pref.enable_skls_export or
            pref.enable_skl_export or
            pref.enable_ogf_export or
            pref.enable_omf_export or
            pref.enable_bones_export
        )

        return panel_used

    def draw(self, context):
        layout = self.layout
        data = context.active_object.data.xray

        verdif = data.check_different_version_bones()
        if verdif != 0:
            ver = props.bone.XRayShapeProps.fmt_version_different(verdif)
            layout.label(
                text=text.get_tip(text.warn.bones_verdif).format(ver),
                icon='ERROR'
            )

        layout.prop(data, 'display_bone_shapes', toggle=True)

        # mass
        col = layout.column(align=True)
        col.prop(data, 'display_bone_mass_centers', toggle=True)

        row = col.row(align=True)
        row.active = data.display_bone_mass_centers
        row.prop(data, 'bone_mass_center_cross_size')

        # joint limits
        col = layout.column(align=True)
        col.prop(data, 'display_bone_limits', toggle=True)

        column = col.column(align=True)
        column.active = data.display_bone_limits
        column.prop(data, 'display_bone_limits_radius')

        row = column.row(align=True)
        row.prop(data, 'display_bone_limit_x', toggle=True)
        row.prop(data, 'display_bone_limit_y', toggle=True)
        row.prop(data, 'display_bone_limit_z', toggle=True)

        row = layout.row(align=True)
        row.label(text='Use Limits:')
        row.prop(data, 'joint_limits_type', expand=True)


def register():
    bpy.utils.register_class(XRAY_PT_armature)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_armature)
