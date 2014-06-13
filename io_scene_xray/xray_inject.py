import bpy
from .xray_inject_ui import inject_ui_init, inject_ui_done


class XRayObjectRevisionProperties(bpy.types.PropertyGroup):
    owner = bpy.props.StringProperty(name='owner')
    ctime = bpy.props.IntProperty(name='ctime')
    moder = bpy.props.StringProperty(name='moder')
    mtime = bpy.props.IntProperty(name='mtime')


class XRayObjectProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Object
    flags = bpy.props.IntProperty(name='flags')
    lodref = bpy.props.StringProperty(name='lodref')
    userdata = bpy.props.StringProperty(name='userdata')
    bpy.utils.register_class(XRayObjectRevisionProperties)
    revision = bpy.props.PointerProperty(type=XRayObjectRevisionProperties)
    motionrefs = bpy.props.StringProperty()


class XRayMeshProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Mesh
    flags = bpy.props.IntProperty(name='flags')
    options = bpy.props.IntVectorProperty(size=2)


class XRayMaterialProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Material
    flags = bpy.props.IntProperty(name='flags')
    eshader = bpy.props.StringProperty(name='eshader')
    cshader = bpy.props.StringProperty(name='cshader')
    gamemtl = bpy.props.StringProperty(name='gamemtl')


class XRayBoneProperties(bpy.types.PropertyGroup):
    class BreakProperties(bpy.types.PropertyGroup):
        force = bpy.props.FloatProperty()
        torque = bpy.props.FloatProperty()

    class ShapeProperties(bpy.types.PropertyGroup):
        type = bpy.props.EnumProperty(items=(
            ('0', 'None', ''),
            ('1', 'Box', ''),
            ('2', 'Sphere', ''),
            ('3', 'Cylinder', '')))
        flags = bpy.props.IntProperty()
        box_rot = bpy.props.FloatVectorProperty(size=9)
        box_trn = bpy.props.FloatVectorProperty()
        box_hsz = bpy.props.FloatVectorProperty()
        sph_pos = bpy.props.FloatVectorProperty()
        sph_rad = bpy.props.FloatProperty()
        cyl_pos = bpy.props.FloatVectorProperty()
        cyl_dir = bpy.props.FloatVectorProperty()
        cyl_hgh = bpy.props.FloatProperty()
        cyl_rad = bpy.props.FloatProperty()

    class IKJointProperties(bpy.types.PropertyGroup):
        type = bpy.props.EnumProperty(items=(
            ('0', 'Rigid', ''),
            ('1', 'Cloth', ''),
            ('2', 'Joint', ''),
            ('3', 'Wheel', ''),
            ('4', 'None', ''),
            ('5', 'Slider', '')))
        lim_x = bpy.props.FloatVectorProperty(size=2)
        lim_x_spr = bpy.props.FloatProperty()
        lim_x_dmp = bpy.props.FloatProperty()
        lim_y = bpy.props.FloatVectorProperty(size=2)
        lim_y_spr = bpy.props.FloatProperty()
        lim_y_dmp = bpy.props.FloatProperty()
        lim_z = bpy.props.FloatVectorProperty(size=2)
        lim_z_spr = bpy.props.FloatProperty()
        lim_z_dmp = bpy.props.FloatProperty()
        spring = bpy.props.FloatProperty()
        damping = bpy.props.FloatProperty()

    class MassProperties(bpy.types.PropertyGroup):
        value = bpy.props.FloatProperty()
        center = bpy.props.FloatVectorProperty()

    b_type = bpy.types.Bone
    length = bpy.props.FloatProperty()
    gamemtl = bpy.props.StringProperty()
    bpy.utils.register_class(ShapeProperties)
    shape = bpy.props.PointerProperty(type=ShapeProperties)
    ikflags = bpy.props.IntProperty()
    bpy.utils.register_class(IKJointProperties)
    ikjoint = bpy.props.PointerProperty(type=IKJointProperties)
    bpy.utils.register_class(BreakProperties)
    breakf = bpy.props.PointerProperty(type=BreakProperties)
    friction = bpy.props.FloatProperty()
    bpy.utils.register_class(MassProperties)
    mass = bpy.props.PointerProperty(type=MassProperties)


classes = [
    XRayObjectProperties
    , XRayMeshProperties
    , XRayMaterialProperties
    , XRayBoneProperties
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
