import bpy

from ..version_utils import assign_props


joint_limit_type_items = (
    ('IK', 'IK Limits', ''),
    ('XRAY', 'X-Ray Limits', '')
)
xray_armature_properties = {
    'display_bone_shapes': bpy.props.BoolProperty(
        name='Display Bone Shapes', default=False
    ),

    'joint_limits_type': bpy.props.EnumProperty(
        items=joint_limit_type_items, name='Export Limits From', default='IK'
    ),
    'display_bone_limits': bpy.props.BoolProperty(
        name='Display Bone Limits', default=False
    ),
    'display_bone_limits_radius': bpy.props.FloatProperty(
        name='Gizmo Radius', default=0.1, min=0.0
    ),
    'display_bone_limit_x': bpy.props.BoolProperty(name='Limit X', default=True),
    'display_bone_limit_y': bpy.props.BoolProperty(name='Limit Y', default=True),
    'display_bone_limit_z': bpy.props.BoolProperty(name='Limit Z', default=True)
}


class XRayArmatureProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Armature

    def check_different_version_bones(self):
        from functools import reduce
        return reduce(
            lambda x, y: x | y,
            [b.xray.shape.check_version_different() for b in self.id_data.bones],
            0,
        )


assign_props([
    (xray_armature_properties, XRayArmatureProperties),
])
