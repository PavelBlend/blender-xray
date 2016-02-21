import bgl
import bpy
import math
import mathutils
from .xray_inject_ui import inject_ui_init, inject_ui_done
from .plugin_prefs import get_preferences


class XRayObjectRevisionProperties(bpy.types.PropertyGroup):
    owner = bpy.props.StringProperty(name='owner')
    ctime = bpy.props.IntProperty(name='ctime')
    moder = bpy.props.StringProperty(name='moder')
    mtime = bpy.props.IntProperty(name='mtime')


def gen_flag_prop(mask, description='', customprop=''):
    def getter(self):
        return self.flags & mask

    def setter(self, value):
        self.flags = self.flags | mask if value else self.flags & ~mask
        if customprop and hasattr(self, customprop):
            setattr(self, customprop, True)

    return bpy.props.BoolProperty(description=description, get=getter, set=setter, options={'SKIP_SAVE'})


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

    _flags_simple_inv_map = [
        None,  # other
        0x20,  # sound occluder
        0x14,  # multi. usage
        0x08,  # hom
        0x03,  # dynamic progressive
        0x01,  # dynamic
        0x00   # static
    ]
    _flags_simple_map = {v: k for k, v in enumerate(_flags_simple_inv_map)}
    flags_force_custom = bpy.props.BoolProperty(options={'SKIP_SAVE'})
    flags_use_custom = bpy.props.BoolProperty(options={'SKIP_SAVE'}, get=lambda self:self.flags_force_custom or not (self.flags in self._flags_simple_map))

    def set_custom_type(self, value):
        self.flags = self.flags | 0x1 if value else self.flags & ~0x1
        self.flags_force_custom = True

    flags_custom_type = bpy.props.EnumProperty(name='Custom Object Type', items=(
        ('st', 'Static', ''),
        ('dy', 'Dynamic', '')), options={'SKIP_SAVE'}, get=lambda self: self.flags & 0x1, set=set_custom_type)
    flags_custom_progressive = gen_flag_prop(mask=0x02, description='Make Progressive', customprop='flags_force_custom')
    flags_custom_lod = gen_flag_prop(mask=0x04, description='Using LOD', customprop='flags_force_custom')
    flags_custom_hom = gen_flag_prop(mask=0x08, description='Hierarchical Occlusion Mapping', customprop='flags_force_custom')
    flags_custom_musage = gen_flag_prop(mask=0x10, customprop='flags_force_custom')
    flags_custom_soccl = gen_flag_prop(mask=0x20, customprop='flags_force_custom')
    flags_custom_hqexp = gen_flag_prop(mask=0x40, description='HQ Geometry', customprop='flags_force_custom')

    def flags_simple_get(self):
        if self.flags_force_custom:
            return 0
        return self._flags_simple_map.get(self.flags, 0)

    def flags_simple_set(self, value):
        self.flags_force_custom = value == 0
        if value != 0:  # !custom
            self.flags = self._flags_simple_inv_map[value]

    flags_simple = bpy.props.EnumProperty(name='Object Type', items=(
        ('??', 'Custom', ''),
        ('so', 'Sound Occluder', ''),
        ('mu', 'Multiple Usage', ''),
        ('ho', 'HOM', 'Hierarchical Occlusion Mapping'),
        ('pd', 'Progressive Dynamic', ''),
        ('dy', 'Dynamic', ''),
        ('st', 'Static', '')), options={'SKIP_SAVE'}, get=flags_simple_get, set=flags_simple_set)
    lodref = bpy.props.StringProperty(name='lodref')
    userdata = bpy.props.StringProperty(name='userdata')
    bpy.utils.register_class(XRayObjectRevisionProperties)
    revision = bpy.props.PointerProperty(type=XRayObjectRevisionProperties)
    motionrefs = bpy.props.StringProperty()


class XRayMeshProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Mesh
    flags = bpy.props.IntProperty(name='flags', default=0x1)
    flags_visible = gen_flag_prop(mask=0x01)
    flags_locked = gen_flag_prop(mask=0x02)
    flags_sgmask = gen_flag_prop(mask=0x04)
    # flags_other = gen_other_flags_prop(mask=~0x01)


def _create_xr_selector(name, pname, default, pref_prop, fparser):
    prop = bpy.props.StringProperty(default=default)

    class State:
        def __init__(self):
            self._cdata = None
            self._cpath = None
            self.other = False

        def get_values(self):
            fpath = getattr(get_preferences(), pref_prop, None)
            if self._cdata and (self._cpath == fpath):
                return self._cdata
            tmp = [('Custom', 'Custom ' + pname)]
            if fpath:
                from io import open
                with open(fpath, mode='rb') as f:
                    for (n, d) in fparser(f.read()):
                        tmp.append((n, d))
            tmp = sorted(tmp, key=lambda e: e[0])
            # print('cache-reload', fpath, len(tmp))
            self._cpath = fpath
            self._cdata = (tmp, {v[0]: k for k, v in enumerate(tmp)})
            return self._cdata

    state = State()

    def get_enum(self):
        if state.other:
            return 0
        return state.get_values()[1].get(getattr(self, name), 0)

    def set_enum(self, value):
        if value == 0:  # custom
            state.other = True
        else:
            state.other = False
            setattr(self, name, state.get_values()[0][value][0])

    prop_enum = bpy.props.EnumProperty(name=pname, items=lambda self, context: ((n, n, d) for n, d in state.get_values()[0]),
                                       get=get_enum, set=set_enum,
                                       options={'SKIP_SAVE'})
    return prop, prop_enum


def _parse_gamemtl(data):
    from .xray_io import ChunkedReader, PackedReader
    for (cid, data) in ChunkedReader(data):
        if cid == 4098:
            for (_, cdata) in ChunkedReader(data):
                name, desc = None, None
                for (cccid, ccdata) in ChunkedReader(cdata):
                    if cccid == 0x1000:
                        pr = PackedReader(ccdata)
                        pr.getf('I')[0]
                        name = pr.gets()
                    if cccid == 0x1005:
                        desc = PackedReader(ccdata).gets()
                yield (name, desc)


def _parse_shaders(data):
    from .xray_io import ChunkedReader, PackedReader
    for (cid, data) in ChunkedReader(data):
        if cid == 3:
            pr = PackedReader(data)
            for i in range(pr.getf('I')[0]):
                yield (pr.gets(), '')


def _parse_shaders_xrlc(data):
    from .xray_io import PackedReader
    if len(data) % (128 + 16) != 0:
        exit(1)
    pr = PackedReader(data)
    for _ in range(len(data) // (128+16)):
        n = pr.gets()
        pr.getf('{}s'.format(127 - len(n) + 16))  # skip
        yield (n, '')


class XRayMaterialProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Material
    flags = bpy.props.IntProperty(name='flags')
    flags_twosided = gen_flag_prop(mask=0x01)
    eshader, eshader_enum = _create_xr_selector('eshader', 'EShader', 'models\\model', 'eshader_file', _parse_shaders)
    cshader, cshader_enum = _create_xr_selector('cshader', 'CShader', 'default', 'cshader_file', _parse_shaders_xrlc)
    gamemtl, gamemtl_enum = _create_xr_selector('gamemtl', 'GameMtl', 'default', 'gamemtl_file', _parse_gamemtl)


class XRayArmatureProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Armature
    version = bpy.props.IntProperty()
    display_bone_shapes = bpy.props.BoolProperty(name='Display Bone Shapes', default=False)


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
    gamemtl, gamemtl_enum = _create_xr_selector('gamemtl', 'gamemtl', 'default_object', 'gamemtl_file', _parse_gamemtl)
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

    def ondraw_postview(self, obj_arm, bone):
        if obj_arm.hide or not obj_arm.data.xray.display_bone_shapes:
            return

        from .gl_utils import matrix_to_buffer, draw_wire_cube, draw_wire_sphere, draw_wire_cylinder

        shape = self.shape
        if shape.type == '0':
            return
        bgl.glEnable(bgl.GL_BLEND)
        if bpy.context.active_bone and (bpy.context.active_bone.id_data == obj_arm.data) and (bpy.context.active_bone.name == bone.name):
            bgl.glColor4f(1.0, 0.0, 0.0, 0.7)
        else:
            bgl.glColor4f(0.0, 0.0, 1.0, 0.5)
        prev_line_width = bgl.Buffer(bgl.GL_FLOAT, [1])
        bgl.glGetFloatv(bgl.GL_LINE_WIDTH, prev_line_width)
        bgl.glPushMatrix()
        try:
            m = obj_arm.matrix_world * obj_arm.pose.bones[bone.name].matrix * mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
            bgl.glLineWidth(2)
            if shape.type == '1':  # box
                rt = shape.box_rot
                mr = mathutils.Matrix((rt[0:3], rt[3:6], rt[6:9])).transposed()
                m *= mathutils.Matrix.Translation(shape.box_trn) * mr.to_4x4()
                bgl.glMultMatrixf(matrix_to_buffer(m.transposed()))
                draw_wire_cube(*shape.box_hsz)
            if shape.type == '2':  # sphere
                m *= mathutils.Matrix.Translation(shape.sph_pos)
                bgl.glMultMatrixf(matrix_to_buffer(m.transposed()))
                draw_wire_sphere(shape.sph_rad, 16)
            if shape.type == '3':  # cylinder
                m *= mathutils.Matrix.Translation(shape.cyl_pos)
                bgl.glMultMatrixf(matrix_to_buffer(m.transposed()))
                v_dir = mathutils.Vector(shape.cyl_dir)
                v_rot = v_dir.cross((0, 1, 0))
                q_rot = mathutils.Quaternion(v_rot.normalized(), math.asin(max(min(v_rot.length, 1), -1)))
                bgl.glMultMatrixf(matrix_to_buffer(q_rot.to_matrix().to_4x4()))
                draw_wire_cylinder(shape.cyl_rad, shape.cyl_hgh * 0.5, 16)
        finally:
            bgl.glPopMatrix()
            bgl.glLineWidth(prev_line_width[0])


classes = [
    XRayObjectProperties
    , XRayMeshProperties
    , XRayMaterialProperties
    , XRayArmatureProperties
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
