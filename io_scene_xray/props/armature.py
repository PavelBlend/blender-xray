# standart modules
import functools

# blender modules
import bpy

# addon modules
from .. import utils


arm_props = {
    'display_bone_shapes': bpy.props.BoolProperty(
        name='Display Bone Shapes',
        default=False
    ),
    'display_bone_mass_centers': bpy.props.BoolProperty(
        name='Display Bone Mass Centers',
        default=False
    ),
    'bone_mass_center_cross_size': bpy.props.FloatProperty(
        name='Cross Size',
        default=0.02,
        min=0.00001,
        precision=5
    ),
    'joint_limits_type': bpy.props.EnumProperty(
        items=(
            ('IK', 'IK', ''),
            # Added a space to the beginning and end of
            # the string so that the translation does not work.
            ('XRAY', ' X-Ray ', '')
        ),
        name='Export Limits From',
        default='IK'
    ),
    'display_bone_limits': bpy.props.BoolProperty(
        name='Display Bone Limits',
        default=False
    ),
    'display_bone_limits_radius': bpy.props.FloatProperty(
        name='Gizmo Radius',
        default=0.1,
        min=0.00001,
        precision=5
    ),
    'display_bone_limit_x': bpy.props.BoolProperty(
        name='Limit X',
        default=True
    ),
    'display_bone_limit_y': bpy.props.BoolProperty(
        name='Limit Y',
        default=True
    ),
    'display_bone_limit_z': bpy.props.BoolProperty(
        name='Limit Z',
        default=True
    )
}


class XRayArmatureProps(bpy.types.PropertyGroup):
    b_type = bpy.types.Armature
    props = arm_props

    if not utils.version.IS_28:
        for prop_name, prop_value in arm_props.items():
            exec('{0} = arm_props.get("{0}")'.format(prop_name))

    def check_different_version_bones(self):
        return functools.reduce(
            lambda x, y: x | y,
            [
                bone.xray.shape.check_version_different()
                for bone in self.id_data.bones
            ],
            0,
        )


def register():
    utils.version.register_prop_group(XRayArmatureProps)


def unregister():
    utils.version.unregister_prop_group(XRayArmatureProps)
