# blender modules
import bpy

# addon modules
from . import material
from .. import ui
from .. import text
from .. import utils
from .. import ops


class XRAY_PT_bone(ui.base.XRayPanel):
    bl_context = 'bone'
    bl_label = ui.base.build_label('Bone')

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if not obj:
            return

        if obj.type != 'ARMATURE':
            return

        if not context.active_bone:
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
        obj = context.active_object
        bone_name = context.active_bone.name
        bone = obj.data.bones.get(bone_name, None)

        if not bone:
            return

        data = bone.xray

        layout = self.layout

        layout.prop(
            data,
            'exportable',
            text=text.get_iface(text.iface.exportable),
            toggle=True,
            translate=False
        )

        layout.separator()

        main_col = layout.column(align=False)
        main_col.enabled = data.exportable

        general_box = main_col.box()
        material.gen_xr_selector(general_box, data, 'gamemtl', 'material', text.get_iface(text.iface.material))
        general_box.prop(data, 'length', text=text.get_iface(text.iface.length))

        main_col.separator()

        box = main_col.box()

        row = box.row()
        row.label(text=text.get_iface(text.iface.shape_type) + ':', translate=False)
        row.prop(data.shape, 'type', text='', translate=False)

        if data.shape.type == '4':
            row = box.row()
            row.label(text=text.get_iface(text.iface.shape_id) + ':', translate=False)
            row.prop(data.shape, 'type_custom_id', text='', translate=False)

        verdif = data.shape.check_version_different()
        if verdif != 0:
            box.label(
                text='shape edited with '
                + data.shape.fmt_version_different(verdif)
                + ' version of this plugin',
                icon='ERROR',
                translate=False
            )

        ops.edit_helpers.bone_shape.HELPER.draw(
            box.column(align=True),
            context
        )

        column = box.column(align=True)

        row = column.row(align=True)
        row.prop(
            data.shape,
            'flags_nopickable',
            text=text.get_iface(text.iface.no_pickable),
            toggle=True,
            translate=False
        )
        row.prop(
            data.shape,
            'flags_nophysics',
            text=text.get_iface(text.iface.no_physics),
            toggle=True,
            translate=False
        )

        row = column.row(align=True)
        row.prop(
            data.shape,
            'flags_removeafterbreak',
            text=text.get_iface(text.iface.remove_after_break),
            toggle=True,
            translate=False
        )
        row.prop(
            data.shape,
            'flags_nofogcollider',
            text=text.get_iface(text.iface.no_fog_collider),
            toggle=True,
            translate=False
        )

        main_col.separator()

        box = main_col.box()

        row = box.row()
        row.label(text=text.get_iface(text.iface.joint_type) + ':', translate=False)
        row.prop(data.ikjoint, 'type', text='', translate=False)

        joint_type = int(data.ikjoint.type)

        if joint_type not in (0, 4):    # 0 - Rigid, 4 - None

            box.prop(data, 'friction', text=text.get_iface(text.iface.friction))

            col = box.column(align=True)
            col.prop(data.ikjoint, 'spring', text=text.get_iface(text.iface.spring))
            col.prop(data.ikjoint, 'damping', text=text.get_iface(text.iface.damping))

            # joint
            if joint_type == 2:
                col_joint = box.column(align=True)
                col_joint.label(text=text.get_iface(text.iface.limit_x) + ':')
                row = col_joint.row(align=True)
                row.prop(data.ikjoint, 'lim_x_min', text=text.get_iface(text.iface.minimum))
                row.prop(data.ikjoint, 'lim_x_max', text=text.get_iface(text.iface.maximum))
                col_joint.prop(data.ikjoint, 'lim_x_spr', text=text.get_iface(text.iface.spring))
                col_joint.prop(data.ikjoint, 'lim_x_dmp', text=text.get_iface(text.iface.damping))

                col_joint = box.column(align=True)
                col_joint.label(text=text.get_iface(text.iface.limit_y) + ':')
                row = col_joint.row(align=True)
                row.prop(data.ikjoint, 'lim_y_min', text=text.get_iface(text.iface.minimum))
                row.prop(data.ikjoint, 'lim_y_max', text=text.get_iface(text.iface.maximum))
                col_joint.prop(data.ikjoint, 'lim_y_spr', text=text.get_iface(text.iface.spring))
                col_joint.prop(data.ikjoint, 'lim_y_dmp', text=text.get_iface(text.iface.damping))

                col_joint = box.column(align=True)
                col_joint.label(text=text.get_iface(text.iface.limit_z) + ':')
                row = col_joint.row(align=True)
                row.prop(data.ikjoint, 'lim_z_min', text=text.get_iface(text.iface.minimum))
                row.prop(data.ikjoint, 'lim_z_max', text=text.get_iface(text.iface.maximum))
                col_joint.prop(data.ikjoint, 'lim_z_spr', text=text.get_iface(text.iface.spring))
                col_joint.prop(data.ikjoint, 'lim_z_dmp', text=text.get_iface(text.iface.damping))

            # wheel
            elif joint_type == 3:
                col_wheel = box.column(align=True)
                col_wheel.label(
                    text=text.get_iface(text.iface.steer_roll),
                    icon='INFO',
                    translate=False
                )
                col_wheel.label(text=text.get_iface(text.iface.steer) + ':')
                col_wheel.prop(data.ikjoint, 'lim_x_min', text=text.get_iface(text.iface.minimum))
                col_wheel.prop(data.ikjoint, 'lim_x_max', text=text.get_iface(text.iface.maximum))

            # slider
            elif joint_type == 5:
                col = box.column(align=True)
                col.label(text=text.get_iface(text.iface.slide_z) + ':')
                row = col.row(align=True)
                row.prop(data.ikjoint, 'slide_min', text=text.get_iface(text.iface.minimum))
                row.prop(data.ikjoint, 'slide_max', text=text.get_iface(text.iface.maximum))
                col.prop(data.ikjoint, 'lim_x_spr', text=text.get_iface(text.iface.spring))
                col.prop(data.ikjoint, 'lim_x_dmp', text=text.get_iface(text.iface.damping))

                col = box.column(align=True)
                col.label(text=text.get_iface(text.iface.rotate_z) + ':')
                row = col.row(align=True)
                row.prop(data.ikjoint, 'lim_y_min', text=text.get_iface(text.iface.minimum))
                row.prop(data.ikjoint, 'lim_y_max', text=text.get_iface(text.iface.maximum))
                col.prop(data.ikjoint, 'lim_y_spr', text=text.get_iface(text.iface.spring))
                col.prop(data.ikjoint, 'lim_y_dmp', text=text.get_iface(text.iface.damping))

            # custom
            elif joint_type == 6:
                row = box.row()
                row.label(text=text.get_iface(text.iface.joint_id) + ':', translate=False)
                row.prop(
                    data.ikjoint,
                    'type_custom_id',
                    text='',
                    translate=False
                )

        col = box.column(align=True)
        col.prop(
            data,
            'ikflags_breakable',
            text=text.get_iface(text.iface.breakable),
            toggle=True,
            translate=False
        )

        if data.ikflags_breakable:
            col.prop(data.breakf, 'force', text=text.get_iface(text.iface.force))
            col.prop(data.breakf, 'torque', text=text.get_iface(text.iface.torque))

        main_col.separator()

        box = main_col.box()

        column = box.column(align=True)
        column.prop(data.mass, 'value')
        column.prop(data.mass, 'center')

        xray = obj.data.xray
        helper = ops.edit_helpers.bone_center.HELPER
        helper.size = xray.bone_mass_center_cross_size
        helper.draw(column, context)


def register():
    bpy.utils.register_class(XRAY_PT_bone)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_bone)
