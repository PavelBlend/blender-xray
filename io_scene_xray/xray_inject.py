import bpy
from .xray_inject_ui import inject_ui_init, inject_ui_done


class XRayObjectProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Object
    flags = bpy.props.IntProperty(name='flags')
    lodref = bpy.props.StringProperty(name='lodref')
    userdata = bpy.props.StringProperty(name='userdata')


class XRayMaterialProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Material
    flags = bpy.props.IntProperty(name='flags')
    eshader = bpy.props.StringProperty(name='eshader')
    cshader = bpy.props.StringProperty(name='cshader')
    gamemtl = bpy.props.StringProperty(name='gamemtl')


classes = [
    XRayObjectProperties
    , XRayMaterialProperties
]


def inject_init():
    for c in classes:
        bpy.utils.register_class(c)
        c.b_type.xray = bpy.props.PointerProperty(type=c)
    inject_ui_init()


def inject_done():
    inject_ui_done()
    for c in classes.reverse():
        del c.b_type.xray
        bpy.utils.unregister_class(c)
