# blender modules
import bpy

# addon modules
from .. import ops
from .. import utils


class XRaySceneProps(bpy.types.PropertyGroup):
    b_type = bpy.types.Scene

    viewer = bpy.props.PointerProperty(type=ops.viewer.XRayViewerProps)


def register():
    utils.version.register_prop_group(XRaySceneProps)


def unregister():
    utils.version.unregister_prop_group(XRaySceneProps)
