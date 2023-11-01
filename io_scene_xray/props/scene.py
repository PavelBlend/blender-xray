# blender modules
import bpy

# addon modules
from .. import ops
from .. import utils


scene_props = {
    'viewer': bpy.props.PointerProperty(type=ops.viewer.XRayViewerProps),
}


class XRaySceneProps(bpy.types.PropertyGroup):
    b_type = bpy.types.Scene
    props = scene_props

    if not utils.version.IS_28:
        for prop_name, prop_value in scene_props.items():
            exec('{0} = scene_props.get("{0}")'.format(prop_name))


def register():
    utils.version.register_prop_group(XRaySceneProps)


def unregister():
    utils.version.unregister_prop_group(XRaySceneProps)
