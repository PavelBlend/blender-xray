# blender modules
import bpy

# addon modules
from . import utils
from ..version_utils import assign_props, IS_28


def gen_other_flags_prop(mask):
    def getter(self):
        return self.flags & mask

    def setter(self, value):
        self.flags = (self.flags & ~mask) | (value & mask)

    return bpy.props.IntProperty(get=getter, set=setter, options={'SKIP_SAVE'})


xray_mesh_properties = {
    'flags': bpy.props.IntProperty(name='flags', default=0x1),
    'flags_visible': utils.gen_flag_prop(mask=0x01),
    'flags_locked': utils.gen_flag_prop(mask=0x02),
    'flags_sgmask': utils.gen_flag_prop(mask=0x04)
}


class XRayMeshProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Mesh

    if not IS_28:
        for prop_name, prop_value in xray_mesh_properties.items():
            exec('{0} = xray_mesh_properties.get("{0}")'.format(prop_name))


prop_groups = (
    (XRayMeshProperties, xray_mesh_properties),
)


def register():
    for prop_group, props in prop_groups:
        assign_props([
            (props, prop_group),
        ])
    bpy.utils.register_class(prop_group)
    prop_group.b_type.xray = bpy.props.PointerProperty(type=prop_group)


def unregister():
    for prop_group, props in reversed(prop_groups):
        del prop_group.b_type.xray
        bpy.utils.unregister_class(prop_group)
