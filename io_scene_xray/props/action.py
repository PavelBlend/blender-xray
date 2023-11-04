# blender modules
import bpy

# addon modules
from . import utility
from .. import utils


_SPECIAL = 0xffff


def _get_collection_item_attr(collection, index, name, special):
    if index == special:
        return ''

    if index < 0 or index >= len(collection):
        return '!{}: index out of range!'.format(index)

    return getattr(collection[index], name)


def _get_collection_index(collection, value, special):
    if not value:
        return special

    return collection.find(value)


def _set_autobake_on(self, value):
    if value:
        self.autobake = 'on'
    else:
        self.autobake = 'off'


def _set_autobake_auto(self, value):
    if value:
        self.autobake = 'auto'
    else:
        self.autobake = 'on'


class XRayActionProps(bpy.types.PropertyGroup):
    b_type = bpy.types.Action

    fps = bpy.props.FloatProperty(
        default=30,
        min=0,
        soft_min=1,
        soft_max=120
    )
    speed = bpy.props.FloatProperty(default=1, min=0, soft_max=10)
    accrue = bpy.props.FloatProperty(default=2, min=0, soft_max=10)
    falloff = bpy.props.FloatProperty(default=2, min=0, soft_max=10)
    power = bpy.props.FloatProperty()

    # flags
    flags = bpy.props.IntProperty()
    flags_fx = utility.gen_flag_prop(
        mask=0x01,
        description='Type FX'
    )
    flags_stopatend = utility.gen_flag_prop(
        mask=0x02,
        description='Stop at end'
    )
    flags_nomix = utility.gen_flag_prop(
        mask=0x04,
        description='No mix'
    )
    flags_syncpart = utility.gen_flag_prop(
        mask=0x08,
        description='Sync part'
    )
    flags_footsteps = utility.gen_flag_prop(
        mask=0x10,
        description='Use Foot Steps'
    )
    flags_movexform = utility.gen_flag_prop(
        mask=0x20,
        description='Move XForm'
    )
    flags_idle = utility.gen_flag_prop(
        mask=0x40,
        description='Idle'
    )
    flags_weaponbone = utility.gen_flag_prop(
        mask=0x80,
        description='Use Weapon Bone'
    )

    # bone or part
    bonepart = bpy.props.IntProperty(default=_SPECIAL)

    bonepart_name = bpy.props.StringProperty(
        get=lambda self: _get_collection_item_attr(
            bpy.context.active_object.pose.bone_groups,
            self.bonepart,
            'name',
            _SPECIAL
        ),
        set=lambda self, value: setattr(
            self, 'bonepart', _get_collection_index(
                bpy.context.active_object.pose.bone_groups,
                value,
                _SPECIAL
            )
        ),
        options={'SKIP_SAVE'}
    )

    bonestart_name = bpy.props.StringProperty(
        get=lambda self: _get_collection_item_attr(
            bpy.context.active_object.pose.bones,
            self.bonepart,
            'name',
            _SPECIAL
        ),
        set=lambda self, value: setattr(
            self, 'bonepart', _get_collection_index(
                bpy.context.active_object.pose.bones,
                value,
                _SPECIAL
            )
        ),
        options={'SKIP_SAVE'}
    )

    # auto bake
    autobake = bpy.props.EnumProperty(
        name='Auto Bake',
        items=(
            ('auto', 'Auto', ''),
            ('on', 'On', ''),
            ('off', 'Off', '')
        ),
        description='Automatically bake this action on each export'
    )
    autobake_auto = bpy.props.BoolProperty(
        name='Auto Bake: Auto',
        get=lambda self: self.autobake == 'auto',
        set=_set_autobake_auto,
        description='Detect when auto-baking is '
            'needed for this action on each export'
    )
    autobake_on = bpy.props.BoolProperty(
        name='Auto Bake',
        get=lambda self: self.autobake == 'on',
        set=_set_autobake_on,
        description='Bake this action on each export'
    )
    autobake_custom_refine = bpy.props.BoolProperty(
        name='Use Custom Thresholds',
        description='Use custom thresholds for remove redundant keyframes'
    )
    autobake_refine_location = bpy.props.FloatProperty(
        default=0.00001,
        min=0,
        soft_max=1,
        subtype='DISTANCE',
        description='Skip threshold for redundant location keyframes'
    )
    autobake_refine_rotation = bpy.props.FloatProperty(
        default=0.00001,
        min=0,
        soft_max=1,
        subtype='ANGLE',
        description='Skip threshold for redundant rotation keyframes'
    )

    def autobake_effective(self, bpy_obj):
        if not self.autobake_auto:
            return self.autobake_on

        if bpy_obj.type == 'ARMATURE':
            for bone in bpy_obj.pose.bones:
                if bone.constraints:
                    return True

        if bpy_obj.constraints:
            return True

        return False


def register():
    utils.version.register_prop_group(XRayActionProps)


def unregister():
    utils.version.unregister_prop_group(XRayActionProps)
