# blender modules
import bpy

# addon modules
from . import utility
from .. import utils


mesh_props = {
    'flags': bpy.props.IntProperty(name='flags', default=0x1),
    'flags_visible': utility.gen_flag_prop(mask=0x01),
    'flags_locked': utility.gen_flag_prop(mask=0x02),
    'flags_sgmask': utility.gen_flag_prop(mask=0x04)
}


class XRayMeshProps(bpy.types.PropertyGroup):
    b_type = bpy.types.Mesh
    props = mesh_props

    if not utils.version.IS_28:
        for prop_name, prop_value in mesh_props.items():
            exec('{0} = mesh_props.get("{0}")'.format(prop_name))


def register():
    utils.version.register_prop_group(XRayMeshProps)


def unregister():
    utils.version.unregister_prop_group(XRayMeshProps)
