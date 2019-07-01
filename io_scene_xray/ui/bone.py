from ..edit_helpers import base, bone_shape, bone_center
from .. import plugin
from .. import registry
from .material import XRayGameMtlMenu, _gen_xr_selector
from .base import XRayPanel, build_label


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


@registry.requires(base, bone_shape, bone_center, XRayGameMtlMenu)
@registry.module_thing
class XRAY_PT_BonePanel(XRayPanel):
    bl_context = 'bone'
    bl_label = build_label('Bone')

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type in {'ARMATURE'}
            and context.active_bone
        )

    def draw_header(self, context):
        layout = self.layout
        bone = context.active_object.data.bones.get(context.active_bone.name, None)
        if not bone:
            return
        data = bone.xray
        layout.label(icon_value=plugin.get_stalker_icon())
        layout.prop(data, 'exportable', text='')

    def draw(self, context):
        layout = self.layout
        bone = context.active_object.data.bones.get(context.active_bone.name, None)
        if not bone:
            return
        data = bone.xray
        layout.enabled = data.exportable
        layout.prop(data, 'length')
        _gen_xr_selector(layout, data, 'gamemtl', 'GameMtl')
        box = layout.box()
        box.prop(data.shape, 'type', text='Shape Type')
        verdif = data.shape.check_version_different()
        if verdif != 0:
            box.label(
                text='shape edited with '
                + data.shape.fmt_version_different(verdif)
                + ' version of this plugin',
                icon='ERROR'
            )
        bone_shape.HELPER.draw(box.column(align=True), context)

        row = box.row(align=True)
        row.prop(data.shape, 'flags_nopickable', text='No Pickable', toggle=True)
        row.prop(data.shape, 'flags_nophysics', text='No Physics', toggle=True)
        row.prop(data.shape, 'flags_removeafterbreak', text='Remove After Break', toggle=True)
        row.prop(data.shape, 'flags_nofogcollider', text='No Fog Collider', toggle=True)
        box = layout.box()
        box.prop(data.ikjoint, 'type', text='Joint Type')
        joint_type = int(data.ikjoint.type)

        if joint_type and joint_type != 4:    # 4 - None type
            if joint_type == 3:    # Wheel
                box.label(text='Steer-X / Roll-Z')
            box.prop(data, 'friction', text='Friction')
            col = box.column(align=True)
            col.prop(data.ikjoint, 'spring', text='Spring')
            col.prop(data.ikjoint, 'damping', text='Damping')

            if joint_type > 1:
                prop_index = 0
                for text in BONE_TEXT[joint_type]:
                    col = box.column(align=True)
                    col.label(text=text[0])
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
        box = layout.box()
        box.prop(data.mass, 'value')
        box.prop(data.mass, 'center')
        bone_center.HELPER.draw(box.column(align=True), context)
