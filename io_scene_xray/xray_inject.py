import bpy
from .xray_inject_ui import inject_ui_init, inject_ui_done


class XRayObjectProperties(bpy.types.PropertyGroup):
    flags = bpy.props.IntProperty(name='flags')
    lodref = bpy.props.StringProperty(name='lodref')
    userdata = bpy.props.StringProperty(name='userdata')


def inject_init():
    bpy.utils.register_class(XRayObjectProperties)
    bpy.types.Object.xray = bpy.props.PointerProperty(type=XRayObjectProperties)
    inject_ui_init()


def inject_done():
    inject_ui_done()
    del bpy.types.Object.xray
    bpy.utils.unregister_class(XRayObjectProperties)
