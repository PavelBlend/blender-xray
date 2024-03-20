# standart modules
import functools

# blender modules
import bpy

# addon modules
from .. import utils


class XRayArmatureProps(bpy.types.PropertyGroup):
    b_type = bpy.types.Armature

    display_bone_shapes = bpy.props.BoolProperty(
        name='Display Bone Shapes',
        default=False
    )
    display_bone_mass_centers = bpy.props.BoolProperty(
        name='Display Bone Mass Centers',
        default=False
    )
    bone_mass_center_cross_size = bpy.props.FloatProperty(
        name='Сrosshair Size',
        default=0.02,
        min=0.00001,
        precision=5
    )
    joint_limits_type = bpy.props.EnumProperty(
        items=(
            ('IK', 'IK', ''),
            # Added a space to the beginning and end of
            # the string so that the translation does not work.
            ('XRAY', ' X-Ray ', '')
        ),
        name='Export Limits From',
        default='IK'
    )
    display_bone_limits = bpy.props.BoolProperty(
        name='Display Bone Limits',
        default=False
    )
    display_bone_limits_radius = bpy.props.FloatProperty(
        name='Gizmo Radius',
        default=0.1,
        min=0.00001,
        precision=5
    )
    display_bone_limit_x = bpy.props.BoolProperty(
        name='Limit X',
        default=True
    )
    display_bone_limit_y = bpy.props.BoolProperty(
        name='Limit Y',
        default=True
    )
    display_bone_limit_z = bpy.props.BoolProperty(
        name='Limit Z',
        default=True
    )

    def check_different_version_bones(self):
        return functools.reduce(
            lambda x, y: x | y,
            [
                bone.xray.shape.check_version_different()
                for bone in self.id_data.bones
            ],
            0,
        )

    def initialize(self, operation, addon_ver):
        if operation == 'LOADED':
            for bone in self.id_data.bones:
                if bone.xray.version < addon_ver:
                    data = bone.xray
                    data.version = addon_ver
                    ik = data.ikjoint
                    ik.slide_min = ik.lim_x_min
                    ik.slide_max = ik.lim_x_max

        elif operation == 'CREATED':
            for bone in self.id_data.bones:
                bone.xray.version = addon_ver


def register():
    utils.version.register_classes(XRayArmatureProps)


def unregister():
    utils.version.unregister_prop_groups(XRayArmatureProps)
