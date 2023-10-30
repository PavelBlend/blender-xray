# blender modules
import bpy

# addon modules
from .. import utils
from .. import ops


import_motion_props = {
    'motion_index': bpy.props.IntProperty(),
}


class ImportSkls(bpy.types.PropertyGroup):
    if not utils.version.IS_28:
        for prop_name, prop_value in import_motion_props.items():
            exec('{0} = import_motion_props.get("{0}")'.format(prop_name))


class ImportOmf(bpy.types.PropertyGroup):
    if not utils.version.IS_28:
        for prop_name, prop_value in import_motion_props.items():
            exec('{0} = import_motion_props.get("{0}")'.format(prop_name))


xray_scene_properties = {
    'import_skls': bpy.props.PointerProperty(type=ImportSkls),
    'import_omf': bpy.props.PointerProperty(type=ImportOmf),
    'viewer': bpy.props.PointerProperty(type=ops.viewer.XRaySceneViewerProperties),
}


class XRaySceneProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Scene

    if not utils.version.IS_28:
        for prop_name, prop_value in xray_scene_properties.items():
            exec('{0} = xray_scene_properties.get("{0}")'.format(prop_name))


prop_groups = (
    (ImportSkls, import_motion_props, False),
    (ImportOmf, import_motion_props, False),
    (XRaySceneProperties, xray_scene_properties, True)
)


def register():
    for prop_group, props, is_group in prop_groups:
        utils.version.assign_props([
            (props, prop_group),
        ])
        bpy.utils.register_class(prop_group)
        if is_group:
            prop_group.b_type.xray = bpy.props.PointerProperty(type=prop_group)


def unregister():
    for prop_group, props, is_group in reversed(prop_groups):
        if is_group:
            del prop_group.b_type.xray
        bpy.utils.unregister_class(prop_group)
