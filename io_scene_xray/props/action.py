import bpy

from . import utils


def _get_collection_item_attr(collection, index, name, special):
    if index == special:
        return ''
    if (index < 0) or (index >= len(collection)):
        return '!' + str(index) + ': index out of range!'
    return getattr(collection[index], name)


def _get_collection_index(collection, value, special):
    if value == '':
        return special
    return collection.find(value)


_SPECIAL = 0xffff


class XRayActionProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Action
    fps = bpy.props.FloatProperty(default=30, min=0, soft_min=1, soft_max=120)
    flags = bpy.props.IntProperty()
    flags_fx = utils.gen_flag_prop(mask=0x01, description='Type FX')
    flags_stopatend = utils.gen_flag_prop(mask=0x02, description='Stop at end')
    flags_nomix = utils.gen_flag_prop(mask=0x04, description='No mix')
    flags_syncpart = utils.gen_flag_prop(mask=0x08, description='Sync part')
    bonepart = bpy.props.IntProperty(default=_SPECIAL)

    bonepart_name = bpy.props.StringProperty(
        get=lambda self: _get_collection_item_attr(
            bpy.context.active_object.pose.bone_groups, self.bonepart,
            'name', _SPECIAL,
        ),
        set=lambda self, value: setattr(self, 'bonepart', _get_collection_index(
            bpy.context.active_object.pose.bone_groups, value, _SPECIAL,
        )),
        options={'SKIP_SAVE'},
    )
    bonestart_name = bpy.props.StringProperty(
        get=lambda self: _get_collection_item_attr(
            bpy.context.active_object.pose.bones, self.bonepart,
            'name', _SPECIAL,
        ),
        set=lambda self, value: setattr(self, 'bonepart', _get_collection_index(
            bpy.context.active_object.pose.bones, value, _SPECIAL,
        )),
        options={'SKIP_SAVE'},
    )
    speed = bpy.props.FloatProperty(default=1, min=0, soft_max=10)
    accrue = bpy.props.FloatProperty(default=2, min=0, soft_max=10)
    falloff = bpy.props.FloatProperty(default=2, min=0, soft_max=10)
    power = bpy.props.FloatProperty()
    autobake = bpy.props.EnumProperty(
        name='Auto Bake',
        items=(
            ('auto', 'Auto', ''),
            ('on', 'On', ''),
            ('off', 'Off', '')
        ),
        description='Automatically bake this action on each export'
    )

    def _set_autobake_auto(self, value):
        self.autobake = 'auto' if value else 'on'

    autobake_auto = bpy.props.BoolProperty(
        name='Auto Bake: Auto',
        get=lambda self: self.autobake == 'auto',
        set=_set_autobake_auto,
        description='Detect when auto-baking is needed for this action on each export'
    )

    def _set_autobake_on(self, value):
        self.autobake = 'on' if value else 'off'

    autobake_on = bpy.props.BoolProperty(
        name='Auto Bake',
        get=lambda self: self.autobake == 'on',
        set=_set_autobake_on,
        description='Bake this action on each export'
    )

    def autobake_effective(self, bobject):
        if not self.autobake_auto:
            return self.autobake_on
        if bobject.type == 'ARMATURE':
            for pbone in bobject.pose.bones:
                if pbone.constraints:
                    return True
        if bobject.constraints:
            return True
        return False

    autobake_custom_refine = bpy.props.BoolProperty(
        name='Custom Thresholds',
        description='Use custom thresholds for remove redundant keyframes'
    )
    autobake_refine_location = bpy.props.FloatProperty(
        default=0.001, min=0, soft_max=1,
        subtype='DISTANCE',
        description='Skip threshold for redundant location keyframes'
    )
    autobake_refine_rotation = bpy.props.FloatProperty(
        default=0.001, min=0, soft_max=1,
        subtype='ANGLE',
        description='Skip threshold for redundant rotation keyframes'
    )
