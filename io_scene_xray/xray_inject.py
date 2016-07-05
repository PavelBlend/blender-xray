import bgl
import bpy
import math
import mathutils
import time
from .xray_inject_ui import inject_ui_init, inject_ui_done
from .plugin_prefs import get_preferences
from . import shape_edit_helper as seh
from . import utils


def _gen_time_prop(prop, description=''):
    fmt = '%Y.%m.%d %H:%M'
    fmt_day = '%Y.%m.%d'

    def getter(self):
        t = getattr(self, prop)
        return time.strftime(fmt, time.localtime(t)) if t else ''

    def setter(self, value):
        value = value.strip()
        t = 0
        if value:
            pt = None
            try:
                pt = time.strptime(value, fmt)
            except ValueError:
                pt = time.strptime(value, fmt_day)
            t = time.mktime(pt)
        setattr(self, prop, t)

    return bpy.props.StringProperty(description=description, get=getter, set=setter, options={'SKIP_SAVE'})


class XRayObjectRevisionProperties(bpy.types.PropertyGroup):
    owner = bpy.props.StringProperty(name='owner')
    ctime = bpy.props.IntProperty(name='ctime')
    ctime_str = _gen_time_prop('ctime', description='Creation time')
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
    class MotionRef(bpy.types.PropertyGroup):
        name = bpy.props.StringProperty()

    def get_isroot(self):
        if not self.root:
            return False
        if utils.is_helper_object(self.id_data):
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

    def userdata_update(self, context):
        if self.userdata == '':
            self.show_userdata = False
    userdata = bpy.props.StringProperty(name='userdata', update=userdata_update)
    show_userdata = bpy.props.BoolProperty(description='View user data', options={'SKIP_SAVE'})
    bpy.utils.register_class(XRayObjectRevisionProperties)
    revision = bpy.props.PointerProperty(type=XRayObjectRevisionProperties)
    motionrefs = bpy.props.StringProperty(description='!Legacy: use \'motionrefs_collection\' instead')
    bpy.utils.register_class(MotionRef)
    motionrefs_collection = bpy.props.CollectionProperty(type=MotionRef)
    motionrefs_collection_index = bpy.props.IntProperty(options={'SKIP_SAVE'})
    show_motionsrefs = bpy.props.BoolProperty(description='View motion refs', options={'SKIP_SAVE'})
    helper_data = bpy.props.StringProperty()


class XRayMeshProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Mesh
    flags = bpy.props.IntProperty(name='flags', default=0x1)
    flags_visible = gen_flag_prop(mask=0x01)
    flags_locked = gen_flag_prop(mask=0x02)
    flags_sgmask = gen_flag_prop(mask=0x04)
    # flags_other = gen_other_flags_prop(mask=~0x01)


class XRayMaterialProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Material
    flags = bpy.props.IntProperty(name='flags')
    flags_twosided = gen_flag_prop(mask=0x01)
    eshader = bpy.props.StringProperty(default='models\\model')
    cshader = bpy.props.StringProperty(default='default')
    gamemtl = bpy.props.StringProperty(default='default')


class XRayArmatureProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Armature
    display_bone_shapes = bpy.props.BoolProperty(name='Display Bone Shapes', default=False)

    def check_different_version_bones(self):
        from functools import reduce
        return reduce(lambda x,y: x|y, [b.xray.shape.check_version_different() for b in self.id_data.bones], 0)


class XRayBoneProperties(bpy.types.PropertyGroup):
    class BreakProperties(bpy.types.PropertyGroup):
        force = bpy.props.FloatProperty()
        torque = bpy.props.FloatProperty()

    class ShapeProperties(bpy.types.PropertyGroup):
        CURVER_DATA = 1

        def check_version_different(self):
            def iszero(vec):
                return not any(v for v in vec)

            if self.version_data == self.CURVER_DATA:
                return 0
            if self.type == '0':  # none
                return 0
            elif self.type == '1':  # box
                if iszero(self.box_trn) and iszero(self.box_rot) and iszero(self.box_hsz):
                    return 0  # default shape
            elif self.type == '2':  # sphere
                if iszero(self.sph_pos) and not self.sph_rad:
                    return 0  # default shape
            elif self.type == '3':  # cylinder
                if iszero(self.cyl_pos) and iszero(self.cyl_dir) and not self.cyl_rad and not self.cyl_hgh:
                    return 0  # default shape
            return 1 if self.version_data < XRayBoneProperties.ShapeProperties.CURVER_DATA else 2

        @staticmethod
        def fmt_version_different(r):
            return 'obsolete' if r == 1 else ('newest' if r == 2 else 'different')

        def update_shape_type(self, context):
            if not self.edit_mode:
                return
            if self.type == '0':
                seh.deactivate()
                return
            seh.activate(bpy.context.active_object.data.bones[bpy.context.active_bone.name], from_chtype=True)

        type = bpy.props.EnumProperty(items=(
            ('0', 'None', ''),
            ('1', 'Box', ''),
            ('2', 'Sphere', ''),
            ('3', 'Cylinder', '')),
            update=update_shape_type
        )
        edit_mode = bpy.props.BoolProperty(
            get=lambda self: seh.is_active(),
            set=lambda self, value: seh.activate(bpy.context.active_object.data.bones[bpy.context.active_bone.name]) if value else seh.deactivate(),
            options={'SKIP_SAVE'}
        )
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
        version_data = bpy.props.IntProperty()

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
                q_rot = v_dir.rotation_difference((0, 1, 0))
                bgl.glMultMatrixf(matrix_to_buffer(q_rot.to_matrix().to_4x4()))
                draw_wire_cylinder(shape.cyl_rad, shape.cyl_hgh * 0.5, 16)
        finally:
            bgl.glPopMatrix()
            bgl.glLineWidth(prev_line_width[0])


def _get_collection_item_attr(collection, index, name, special):
    if index == special:
        return ''
    if (index < 0) or (index >= len(collection)):
        return '!' + str(index) + ': index out of range!'
    return getattr(collection[index], name)


class XRayActionProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Action
    fps = bpy.props.FloatProperty(default=30, min=0, soft_min=1, soft_max=120)
    flags = bpy.props.IntProperty()
    flags_fx = gen_flag_prop(mask=0x01, description='Type FX')
    flags_stopatend = gen_flag_prop(mask=0x02, description='Stop at end')
    flags_nomix = gen_flag_prop(mask=0x04, description='No mix')
    flags_syncpart = gen_flag_prop(mask=0x08, description='Sync part')
    bonepart = bpy.props.IntProperty(default=0xffff)

    def _set_search_collection_item(self, collection, value):
        if value == '':
            self.bonepart = 0xffff
        else:
            self.bonepart = collection.find(value)

    bonepart_name = bpy.props.StringProperty(
        get=lambda self: _get_collection_item_attr(bpy.context.active_object.pose.bone_groups, self.bonepart, 'name', 0xffff),
        set=lambda self, value: self._set_search_collection_item(bpy.context.active_object.pose.bone_groups, value), options={'SKIP_SAVE'}
    )
    bonestart_name = bpy.props.StringProperty(
        get=lambda self: _get_collection_item_attr(bpy.context.active_object.pose.bones, self.bonepart, 'name', 0xffff),
        set=lambda self, value: self._set_search_collection_item(bpy.context.active_object.pose.bones, value), options={'SKIP_SAVE'}
    )
    speed = bpy.props.FloatProperty(default=1, min=0, soft_max=10)
    accrue = bpy.props.FloatProperty(default=2, min=0, soft_max=10)
    falloff = bpy.props.FloatProperty(default=2, min=0, soft_max=10)
    power = bpy.props.FloatProperty()


classes = [
    XRayObjectProperties
    , XRayMeshProperties
    , XRayMaterialProperties
    , XRayArmatureProperties
    , XRayBoneProperties
    , XRayActionProperties
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
