# blender modules
import bpy

# addon modules
from . import material
from .. import ui
from .. import utils
from .. import ops


BONE_TEXT_JOINT = []
for axis in ('X', 'Y', 'Z'):
    BONE_TEXT_JOINT.append((
        'Limit {}'.format(axis),
        ('Min', 'Max'),
        'Spring',
        'Damping'
    ))

BONE_TEXT_WHEEL = [(
    'Steer',
    ('Limit Min', 'Limit Max')
), ]

BONE_TEXT_SLIDER = []
for transform in ('Slide', 'Rotate'):
    BONE_TEXT_SLIDER.append((
        '{} Axis Z'.format(transform),
        ('Limits Min', 'Limits Max'),
        'Spring',
        'Damping'
    ))

BONE_TEXT = {
    2: BONE_TEXT_JOINT,
    3: BONE_TEXT_WHEEL,
    5: BONE_TEXT_SLIDER
}

BONE_PROPS = []
for axis in ('x', 'y', 'z'):
    BONE_PROPS.extend((
        'lim_{}_min'.format(axis),
        'lim_{}_max'.format(axis),
        'lim_{}_spr'.format(axis),
        'lim_{}_dmp'.format(axis)
    ))


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
            text='Exportable',
            toggle=True,
            translate=False
        )

        main_col = layout.column(align=False)
        main_col.enabled = data.exportable

        main_col.prop(data, 'length')

        material.gen_xr_selector(main_col, data, 'gamemtl', 'Material')

        box = main_col.box()

        row = box.row()
        row.label(text='Shape Type:', translate=False)
        row.prop(data.shape, 'type', text='', translate=False)

        if data.shape.type == '4':
            row = box.row()
            row.label(text='Shape ID:', translate=False)
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
            text='No Pickable',
            toggle=True,
            translate=False
        )
        row.prop(
            data.shape,
            'flags_nophysics',
            text='No Physics',
            toggle=True,
            translate=False
        )

        row = column.row(align=True)
        row.prop(
            data.shape,
            'flags_removeafterbreak',
            text='Remove After Break',
            toggle=True,
            translate=False
        )
        row.prop(
            data.shape,
            'flags_nofogcollider',
            text='No Fog Collider',
            toggle=True,
            translate=False
        )

        box = main_col.box()

        row = box.row()
        row.label(text='Joint Type:', translate=False)
        row.prop(data.ikjoint, 'type', text='', translate=False)

        joint_type = int(data.ikjoint.type)

        if joint_type != 4:    # 4 - None type

            box.prop(data, 'friction', text='Friction')

            col = box.column(align=True)
            col.prop(data.ikjoint, 'spring', text='Spring')
            col.prop(data.ikjoint, 'damping', text='Damping')

            # joint
            if joint_type == 2:
                col_joint = box.column(align=True)
                col_joint.label(text='Limit X:')
                row = col_joint.row(align=True)
                row.prop(data.ikjoint, 'lim_x_min', text='Min')
                row.prop(data.ikjoint, 'lim_x_max', text='Max')
                col_joint.prop(data.ikjoint, 'lim_x_spr', text='Spring')
                col_joint.prop(data.ikjoint, 'lim_x_dmp', text='Damping')

                col_joint = box.column(align=True)
                col_joint.label(text='Limit Y:')
                row = col_joint.row(align=True)
                row.prop(data.ikjoint, 'lim_y_min', text='Min')
                row.prop(data.ikjoint, 'lim_y_max', text='Max')
                col_joint.prop(data.ikjoint, 'lim_y_spr', text='Spring')
                col_joint.prop(data.ikjoint, 'lim_y_dmp', text='Damping')

                col_joint = box.column(align=True)
                col_joint.label(text='Limit Z:')
                row = col_joint.row(align=True)
                row.prop(data.ikjoint, 'lim_z_min', text='Min')
                row.prop(data.ikjoint, 'lim_z_max', text='Max')
                col_joint.prop(data.ikjoint, 'lim_z_spr', text='Spring')
                col_joint.prop(data.ikjoint, 'lim_z_dmp', text='Damping')

            # wheel
            elif joint_type == 3:
                col_wheel = box.column(align=True)
                col_wheel.label(
                    text='Steer-X / Roll-Z',
                    icon='INFO',
                    translate=False
                )
                col_wheel.label(text='Steer:')
                col_wheel.prop(data.ikjoint, 'lim_x_min', text='Min')
                col_wheel.prop(data.ikjoint, 'lim_x_max', text='Max')

            # slider
            elif joint_type == 5:
                col = box.column(align=True)
                col.label(text='Slide Z:')
                col.prop(data.ikjoint, 'lim_x_min', text='Min')
                col.prop(data.ikjoint, 'lim_x_max', text='Max')

                col = box.column(align=True)
                col.label(text='Rotate Z:')
                col.prop(data.ikjoint, 'lim_y_min', text='Min')
                col.prop(data.ikjoint, 'lim_y_max', text='Max')

            # custom
            elif joint_type == 6:
                row = box.row()
                row.label(text='Joint ID:', translate=False)
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
            text='Breakable',
            toggle=True,
            translate=False
        )

        if data.ikflags_breakable:
            col.prop(data.breakf, 'force', text='Force')
            col.prop(data.breakf, 'torque', text='Torque')

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
