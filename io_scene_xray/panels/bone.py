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

BONE_TEXT_WHEEL = (('Steer', ('Limit Min', 'Limit Max')), )

BONE_TEXT_SLIDER = []
for transform in ('Slide', 'Rotate'):
    BONE_TEXT_SLIDER.append(
        ('{} Axis Z'.format(transform), ('Limits Min', 'Limits Max'), 'Spring', 'Damping')
    )

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
        preferences = utils.version.get_preferences()
        panel_used = (
            # import formats
            preferences.enable_object_import or
            preferences.enable_skls_import or
            preferences.enable_bones_import or
            preferences.enable_omf_import or
            preferences.enable_ogf_import or
            preferences.enable_part_import or
            # export formats
            preferences.enable_object_export or
            preferences.enable_skls_export or
            preferences.enable_skl_export or
            preferences.enable_bones_export or
            preferences.enable_omf_export or
            preferences.enable_ogf_export
        )
        return (
            context.active_object and
            context.active_object.type in {'ARMATURE'} and
            context.active_bone and
            panel_used
        )

    def draw(self, context):
        obj = context.active_object
        bone_name = context.active_bone.name
        bone = obj.data.bones.get(bone_name, None)
        if not bone:
            return
        data = bone.xray

        layout = self.layout
        layout.prop(data, 'exportable', toggle=True)
        main_col = layout.column(align=False)
        main_col.enabled = data.exportable
        main_col.prop(data, 'length')
        material.gen_xr_selector(main_col, data, 'gamemtl', 'Material')
        box = main_col.box()
        row = box.row()
        row.label(text='Shape Type:')
        row.prop(data.shape, 'type', text='')
        verdif = data.shape.check_version_different()
        if verdif != 0:
            box.label(
                text='shape edited with '
                + data.shape.fmt_version_different(verdif)
                + ' version of this plugin',
                icon='ERROR'
            )
        ops.edit_helpers.bone_shape.HELPER.draw(box.column(align=True), context)

        column = box.column(align=True)
        row = column.row(align=True)
        row.prop(data.shape, 'flags_nopickable', text='No Pickable', toggle=True)
        row.prop(data.shape, 'flags_nophysics', text='No Physics', toggle=True)
        row = column.row(align=True)
        row.prop(data.shape, 'flags_removeafterbreak', text='Remove After Break', toggle=True)
        row.prop(data.shape, 'flags_nofogcollider', text='No Fog Collider', toggle=True)
        box = main_col.box()
        row = box.row()
        row.label(text='Joint Type:')
        row.prop(data.ikjoint, 'type', text='')
        joint_type = int(data.ikjoint.type)

        if joint_type and joint_type != 4:    # 4 - None type
            if joint_type == 3:    # Wheel
                box.label(text='Steer-X / Roll-Z', icon='INFO')
            box.prop(data, 'friction', text='Friction')
            col = box.column(align=True)
            col.prop(data.ikjoint, 'spring', text='Spring')
            col.prop(data.ikjoint, 'damping', text='Damping')

            if joint_type > 1:
                prop_index = 0
                for text in BONE_TEXT[joint_type]:
                    col = box.column(align=True)
                    col.label(text=text[0] + ':')
                    # slider info
                    if joint_type == 5 and text[0] == 'Slide Axis Z':
                        col.label(
                            text='Limit Min: {0:.4f} m'.format(
                                data.ikjoint.lim_x_min
                            ),
                            icon='INFO'
                        )
                        col.label(
                            text='Limit Max: {0:.4f} m'.format(
                                data.ikjoint.lim_x_max
                            ),
                            icon='INFO'
                        )
                    for prop_text in text[1 : ]:
                        if type(prop_text) == tuple:
                            row = col.row(align=True)
                            for property_text in prop_text:
                                row.prop(data.ikjoint, BONE_PROPS[prop_index], text=property_text)
                                prop_index += 1
                        else:
                            col.prop(data.ikjoint, BONE_PROPS[prop_index], text=prop_text)
                            prop_index += 1

        col = box.column(align=True)
        col.prop(data, 'ikflags_breakable', text='Breakable', toggle=True)
        if data.ikflags_breakable:
            col.prop(data.breakf, 'force', text='Force')
            col.prop(data.breakf, 'torque', text='Torque')
        box = main_col.box()
        column = box.column(align=True)
        column.prop(data.mass, 'value')
        column.prop(data.mass, 'center')
        xray = obj.data.xray
        ops.edit_helpers.bone_center.HELPER.size = xray.bone_mass_center_cross_size
        ops.edit_helpers.bone_center.HELPER.draw(column, context)


def register():
    bpy.utils.register_class(XRAY_PT_bone)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_bone)
