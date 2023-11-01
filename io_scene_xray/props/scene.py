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

    if not utils.version.IS_28:
        for prop_name, prop_value in scene_props.items():
            exec('{0} = scene_props.get("{0}")'.format(prop_name))


prop_groups = (
    (XRaySceneProps, scene_props),
)


def register():
    for prop_group, props in prop_groups:
        utils.version.assign_props([
            (props, prop_group),
        ])
        bpy.utils.register_class(prop_group)
        b_type = getattr(prop_group, 'b_type', None)
        if b_type:
            b_type.xray = bpy.props.PointerProperty(type=prop_group)


def unregister():
    for prop_group, props in reversed(prop_groups):
        if hasattr(prop_group, 'b_type'):
            del prop_group.b_type.xray
        bpy.utils.unregister_class(prop_group)
