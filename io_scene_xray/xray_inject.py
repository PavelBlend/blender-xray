import bpy
from .xray_inject_ui import inject_ui_init, inject_ui_done


class XRayObjectRevisionProperties(bpy.types.PropertyGroup):
    owner = bpy.props.StringProperty(name='owner')
    ctime = bpy.props.IntProperty(name='ctime')
    moder = bpy.props.StringProperty(name='moder')
    mtime = bpy.props.IntProperty(name='mtime')


def gen_flag_prop(mask):
    def getter(self):
        return self.flags & mask

    def setter(self, value):
        self.flags = self.flags | mask if value else self.flags & ~mask

    return bpy.props.BoolProperty(get=getter, set=setter, options={'SKIP_SAVE'})


def gen_other_flags_prop(mask):
    def getter(self):
        return self.flags & mask

    def setter(self, value):
        self.flags = (self.flags & ~mask) | (value & mask)

    return bpy.props.IntProperty(get=getter, set=setter, options={'SKIP_SAVE'})


class XRayObjectProperties(bpy.types.PropertyGroup):
    def get_isroot(self):
        if not self.root:
            return False
        if self.id_data.parent:
            return not self.id_data.parent.xray.isroot
        return True

    def set_isroot(self, value):
        if self.id_data.parent:
            self.id_data.parent.xray.isroot = not value
        self.root = value

    b_type = bpy.types.Object
    root = bpy.props.BoolProperty(default=True)  # default=True - to backward compatibility
    isroot = bpy.props.BoolProperty(get=get_isroot, set=set_isroot, options={'SKIP_SAVE'})
    version = bpy.props.IntProperty()
    flags = bpy.props.IntProperty(name='flags')
    flags_dynamic = gen_flag_prop(mask=0x01)
    flags_progressive = gen_flag_prop(mask=0x02)
    flags_other = gen_other_flags_prop(mask=~0x03)
    lodref = bpy.props.StringProperty(name='lodref')
    userdata = bpy.props.StringProperty(name='userdata')
    bpy.utils.register_class(XRayObjectRevisionProperties)
    revision = bpy.props.PointerProperty(type=XRayObjectRevisionProperties)
    motionrefs = bpy.props.StringProperty()


class XRayMeshProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Mesh
    flags = bpy.props.IntProperty(name='flags', default=0x1)
    flags_valid = gen_flag_prop(mask=0x01)
    flags_other = gen_other_flags_prop(mask=~0x01)
    options = bpy.props.IntVectorProperty(size=2)


class XRayMaterialProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Material
    flags = bpy.props.IntProperty(name='flags')
    flags_twosided = gen_flag_prop(mask=0x01)
    eshader = bpy.props.StringProperty(name='eshader', default='models\\model')
    cshader = bpy.props.StringProperty(name='cshader', default='default')
    gamemtl = bpy.props.StringProperty(name='gamemtl', default='default')


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
        flags_nopickable = gen_flag_prop(mask=0x1)
        flags_removeafterbreak = gen_flag_prop(mask=0x2)
        flags_nophysics = gen_flag_prop(mask=0x4)
        flags_nofogcollider = gen_flag_prop(mask=0x8)
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
        lim_x_spr = bpy.props.FloatProperty()
        lim_x_dmp = bpy.props.FloatProperty()
        lim_y_spr = bpy.props.FloatProperty()
        lim_y_dmp = bpy.props.FloatProperty()
        lim_z_spr = bpy.props.FloatProperty()
        lim_z_dmp = bpy.props.FloatProperty()
        spring = bpy.props.FloatProperty()
        damping = bpy.props.FloatProperty()

    class MassProperties(bpy.types.PropertyGroup):
        value = bpy.props.FloatProperty()
        center = bpy.props.FloatVectorProperty()

    b_type = bpy.types.Bone
    version = bpy.props.IntProperty()
    length = bpy.props.FloatProperty()
    gamemtl = bpy.props.StringProperty(default='default_object')
    bpy.utils.register_class(ShapeProperties)
    shape = bpy.props.PointerProperty(type=ShapeProperties)
    ikflags = bpy.props.IntProperty()

    def set_ikflags_breakable(self, value):
        self.ikflags = self.ikflags | 0x1 if value else self.ikflags & ~0x1

    ikflags_breakable = bpy.props.BoolProperty(get=lambda self: self.ikflags & 0x1, set=set_ikflags_breakable, options={'SKIP_SAVE'})
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
    for c in reversed(classes):
        del c.b_type.xray
        bpy.utils.unregister_class(c)
