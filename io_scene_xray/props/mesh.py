# blender modules
import bpy

# addon modules
from . import utility
from .. import utils


class XRayMeshProps(bpy.types.PropertyGroup):
    b_type = bpy.types.Mesh

    flags = bpy.props.IntProperty(name='flags', default=0x1)
    flags_visible = utility.gen_flag_prop(mask=0x01)
    flags_locked = utility.gen_flag_prop(mask=0x02)
    flags_sgmask = utility.gen_flag_prop(mask=0x04)


def register():
    utils.version.register_classes(XRayMeshProps)


def unregister():
    utils.version.unregister_prop_groups(XRayMeshProps)
