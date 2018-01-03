import time

import bgl
import bpy
import mathutils

from .plugin_prefs import PropObjectMotionsExport, PropObjectTextureNamesFromPath, PropSDKVersion
from . import shape_edit_helper as seh
from . import utils
from . import registry


def _gen_time_prop(prop, description=''):
    fmt = '%Y.%m.%d %H:%M'
    fmt_day = '%Y.%m.%d'

    def getter(self):
        tval = getattr(self, prop)
        return time.strftime(fmt, time.localtime(tval)) if tval else ''

    def setter(self, value):
        value = value.strip()
        tval = 0
        if value:
            ptime = None
            try:
                ptime = time.strptime(value, fmt)
            except ValueError:
                ptime = time.strptime(value, fmt_day)
            tval = time.mktime(ptime)
        setattr(self, prop, tval)

    return bpy.props.StringProperty(
        description=description,
        get=getter, set=setter,
        options={'SKIP_SAVE'}
    )


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

    return bpy.props.BoolProperty(
        description=description,
        get=getter, set=setter,
        options={'SKIP_SAVE'}
    )


def gen_other_flags_prop(mask):
    def getter(self):
        return self.flags & mask

    def setter(self, value):
        self.flags = (self.flags & ~mask) | (value & mask)

    return bpy.props.IntProperty(get=getter, set=setter, options={'SKIP_SAVE'})


@registry.requires(XRayObjectRevisionProperties, 'MotionRef')
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
    flags_use_custom = bpy.props.BoolProperty(
        options={'SKIP_SAVE'},
        get=lambda self: self.flags_force_custom or not (self.flags in self._flags_simple_map)
    )

    def set_custom_type(self, value):
        self.flags = self.flags | 0x1 if value else self.flags & ~0x1
        self.flags_force_custom = True

    flags_custom_type = bpy.props.EnumProperty(
        name='Custom Object Type',
        items=(
            ('st', 'Static', ''),
            ('dy', 'Dynamic', '')
        ),
        options={'SKIP_SAVE'},
        get=lambda self: self.flags & 0x1, set=set_custom_type
    )
    flags_custom_progressive = gen_flag_prop(
        mask=0x02,
        description='Make Progressive',
        customprop='flags_force_custom'
    )
    flags_custom_lod = gen_flag_prop(
        mask=0x04,
        description='Using LOD',
        customprop='flags_force_custom'
    )
    flags_custom_hom = gen_flag_prop(
        mask=0x08,
        description='Hierarchical Occlusion Mapping',
        customprop='flags_force_custom'
    )
    flags_custom_musage = gen_flag_prop(
        mask=0x10,
        customprop='flags_force_custom'
    )
    flags_custom_soccl = gen_flag_prop(
        mask=0x20,
        customprop='flags_force_custom'
    )
    flags_custom_hqexp = gen_flag_prop(
        mask=0x40,
        description='HQ Geometry',
        customprop='flags_force_custom'
    )

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
    lodref = bpy.props.StringProperty(name='LOD Reference')

    def userdata_update(self, _context):
        if self.userdata == '':
            self.show_userdata = False
    userdata = bpy.props.StringProperty(name='userdata', update=userdata_update)
    show_userdata = bpy.props.BoolProperty(description='View user data', options={'SKIP_SAVE'})
    revision = bpy.props.PointerProperty(type=XRayObjectRevisionProperties)
    motionrefs = bpy.props.StringProperty(
        description='!Legacy: use \'motionrefs_collection\' instead'
    )
    motionrefs_collection = bpy.props.CollectionProperty(type=MotionRef)
    motionrefs_collection_index = bpy.props.IntProperty(options={'SKIP_SAVE'})
    show_motionsrefs = bpy.props.BoolProperty(description='View motion refs', options={'SKIP_SAVE'})
    helper_data = bpy.props.StringProperty()
    export_path = bpy.props.StringProperty(
        name='Export Path',
        description='Path relative to the root export folder'
    )

    # Detail Mesh Options
    no_waving = bpy.props.BoolProperty(
        description='No Waving',
        options={'SKIP_SAVE'},
        default=False
    )
    min_scale = bpy.props.FloatProperty(default=1.0, min=0.1, max=100.0)
    max_scale = bpy.props.FloatProperty(default=1.0, min=0.1, max=100.0)

    def initialize(self, context):
        if not self.version:
            if context.operation == 'LOADED':
                self.version = -1
            elif context.operation == 'CREATED':
                self.version = context.plugin_version_number
                self.root = context.thing.type == 'MESH'


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
    version = bpy.props.IntProperty()

    def initialize(self, context):
        if not self.version:
            if context.operation == 'LOADED':
                self.version = -1
            elif context.operation == 'CREATED':
                self.version = context.plugin_version_number
                obj = bpy.context.active_object
                if obj and obj.xray.flags_custom_type == 'st':
                    self.eshader = 'default'


class XRayArmatureProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Armature
    display_bone_shapes = bpy.props.BoolProperty(name='Display Bone Shapes', default=False)

    def check_different_version_bones(self):
        from functools import reduce
        return reduce(
            lambda x, y: x | y,
            [b.xray.shape.check_version_different() for b in self.id_data.bones],
            0,
        )


def _seh_edit_mode_set(value):
    if value:
        seh.activate(bpy.context.active_object.data.bones[bpy.context.active_bone.name])
    else:
        seh.deactivate()


__MATRIX_IDENTITY__ = mathutils.Matrix.Identity(4)

def _fvec16_to_matrix4(fvec):
    return mathutils.Matrix((fvec[0:4], fvec[4:8], fvec[8:12], fvec[12:16]))

def _is_fvec16_nonzero(fvec):
    for v in fvec:
        if v != 0:
            return True
    return False


@registry.requires('ShapeProperties', 'IKJointProperties', 'BreakProperties', 'MassProperties')
class XRayBoneProperties(bpy.types.PropertyGroup):
    class BreakProperties(bpy.types.PropertyGroup):
        force = bpy.props.FloatProperty()
        torque = bpy.props.FloatProperty()

    class ShapeProperties(bpy.types.PropertyGroup):
        _CURVER_DATA = 1

        def check_version_different(self):
            def iszero(vec):
                return not any(v for v in vec)

            if self.version_data == self._CURVER_DATA:
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
                if iszero(self.cyl_pos) \
                    and iszero(self.cyl_dir) \
                    and not self.cyl_rad \
                    and not self.cyl_hgh:
                    return 0  # default shape
            return 1 if self.version_data < self._CURVER_DATA else 2

        @staticmethod
        def fmt_version_different(res):
            return 'obsolete' if res == 1 else ('newest' if res == 2 else 'different')

        def set_curver(self):
            self.version_data = self._CURVER_DATA

        def update_shape_type(self, _context):
            if not self.edit_mode:
                return
            if self.type == '0':
                seh.deactivate()
                return
            seh.activate(
                bpy.context.active_object.data.bones[bpy.context.active_bone.name],
                from_chtype=True
            )

        type = bpy.props.EnumProperty(
            items=(
                ('0', 'None', ''),
                ('1', 'Box', ''),
                ('2', 'Sphere', ''),
                ('3', 'Cylinder', '')
            ),
            update=update_shape_type
        )

        edit_mode = bpy.props.BoolProperty(
            get=lambda self: seh.is_active(),
            set=lambda self, value: _seh_edit_mode_set(value),
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
        enabled = bpy.props.BoolProperty(default=True)
        is_rigid = bpy.props.BoolProperty(get=lambda self: self.type == '0')

    class MassProperties(bpy.types.PropertyGroup):
        value = bpy.props.FloatProperty()
        center = bpy.props.FloatVectorProperty()

    b_type = bpy.types.Bone
    exportable = bpy.props.BoolProperty(default=True, description='Enable Bone to be exported')
    version = bpy.props.IntProperty()
    length = bpy.props.FloatProperty(name='Length')
    gamemtl = bpy.props.StringProperty(default='default_object')
    shape = bpy.props.PointerProperty(type=ShapeProperties)
    ikflags = bpy.props.IntProperty()

    def set_ikflags_breakable(self, value):
        self.ikflags = self.ikflags | 0x1 if value else self.ikflags & ~0x1

    ikflags_breakable = bpy.props.BoolProperty(
        get=lambda self: self.ikflags & 0x1,
        set=set_ikflags_breakable,
        options={'SKIP_SAVE'}
    )
    ikjoint = bpy.props.PointerProperty(type=IKJointProperties)
    breakf = bpy.props.PointerProperty(type=BreakProperties)
    friction = bpy.props.FloatProperty()
    mass = bpy.props.PointerProperty(type=MassProperties)
    org_matrix = bpy.props.FloatVectorProperty(size=16)

    def matrix_local(self, bone):
        data = self.org_matrix
        if _is_fvec16_nonzero(data):
            return _fvec16_to_matrix4(self.org_matrix)
        return bone.matrix_local

    def matrix_delta(self, bone):
        data = self.org_matrix
        if not _is_fvec16_nonzero(data):
            return __MATRIX_IDENTITY__
        return _fvec16_to_matrix4(data).inverted() * bone.matrix_local

    def ondraw_postview(self, obj_arm, bone):
        if obj_arm.hide or not obj_arm.data.xray.display_bone_shapes:
            return

        from .gl_utils import matrix_to_buffer, draw_wire_cube, draw_wire_sphere, draw_wire_cylinder

        shape = self.shape
        if shape.type == '0':
            return
        bgl.glEnable(bgl.GL_BLEND)
        if bpy.context.active_bone \
            and (bpy.context.active_bone.id_data == obj_arm.data) \
            and (bpy.context.active_bone.name == bone.name):
            bgl.glColor4f(1.0, 0.0, 0.0, 0.7)
        else:
            bgl.glColor4f(0.0, 0.0, 1.0, 0.5)
        prev_line_width = bgl.Buffer(bgl.GL_FLOAT, [1])
        bgl.glGetFloatv(bgl.GL_LINE_WIDTH, prev_line_width)
        bgl.glPushMatrix()
        try:
            matrix_pose = obj_arm.pose.bones[bone.name].matrix
            org_matrix = self.org_matrix
            if _is_fvec16_nonzero(org_matrix):
                matrix_pose *= bone.matrix_local.inverted() * _fvec16_to_matrix4(org_matrix)
            mat = obj_arm.matrix_world * matrix_pose * mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
            bgl.glLineWidth(2)
            if shape.type == '1':  # box
                rot = shape.box_rot
                mat *= mathutils.Matrix.Translation(shape.box_trn) \
                    * mathutils.Matrix((rot[0:3], rot[3:6], rot[6:9])).transposed().to_4x4()
                bgl.glMultMatrixf(matrix_to_buffer(mat.transposed()))
                draw_wire_cube(*shape.box_hsz)
            if shape.type == '2':  # sphere
                mat *= mathutils.Matrix.Translation(shape.sph_pos)
                bgl.glMultMatrixf(matrix_to_buffer(mat.transposed()))
                draw_wire_sphere(shape.sph_rad, 16)
            if shape.type == '3':  # cylinder
                mat *= mathutils.Matrix.Translation(shape.cyl_pos)
                bgl.glMultMatrixf(matrix_to_buffer(mat.transposed()))
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


def _get_collection_index(collection, value, special):
    if value == '':
        return special
    return collection.find(value)


_SPECIAL = 0xffff

class XRayActionProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Action
    fps = bpy.props.FloatProperty(default=30, min=0, soft_min=1, soft_max=120)
    flags = bpy.props.IntProperty()
    flags_fx = gen_flag_prop(mask=0x01, description='Type FX')
    flags_stopatend = gen_flag_prop(mask=0x02, description='Stop at end')
    flags_nomix = gen_flag_prop(mask=0x04, description='No mix')
    flags_syncpart = gen_flag_prop(mask=0x08, description='Sync part')
    bonepart = bpy.props.IntProperty(default=_SPECIAL)

    bonepart_name = bpy.props.StringProperty(
        get=lambda self: _get_collection_item_attr(
            bpy.context.active_object.pose.bone_groups, self.bonepart,
            'name', _SPECIAL,
        ),
        set=lambda self, value: setattr(self, 'bonepart', _get_collection_index(
            bpy.context.active_object.pose.bone_groups, value, _SPECIAL,
        )),
        options={'SKIP_SAVE'},
    )
    bonestart_name = bpy.props.StringProperty(
        get=lambda self: _get_collection_item_attr(
            bpy.context.active_object.pose.bones, self.bonepart,
            'name', _SPECIAL,
        ),
        set=lambda self, value: setattr(self, 'bonepart', _get_collection_index(
            bpy.context.active_object.pose.bones, value, _SPECIAL,
        )),
        options={'SKIP_SAVE'},
    )
    speed = bpy.props.FloatProperty(default=1, min=0, soft_max=10)
    accrue = bpy.props.FloatProperty(default=2, min=0, soft_max=10)
    falloff = bpy.props.FloatProperty(default=2, min=0, soft_max=10)
    power = bpy.props.FloatProperty()
    autobake = bpy.props.EnumProperty(
        name='Auto Bake',
        items=(
            ('auto', 'Auto', ''),
            ('on', 'On', ''),
            ('off', 'Off', '')
        ),
        description='Automatically bake this action on each export'
    )

    def _set_autobake_auto(self, value):
        self.autobake = 'auto' if value else 'on'

    autobake_auto = bpy.props.BoolProperty(
        name='Auto Bake: Auto',
        get=lambda self: self.autobake == 'auto',
        set=_set_autobake_auto,
        description='Detect when auto-baking is needed for this action on each export'
    )

    def _set_autobake_on(self, value):
        self.autobake = 'on' if value else 'off'

    autobake_on = bpy.props.BoolProperty(
        name='Auto Bake',
        get=lambda self: self.autobake == 'on',
        set=_set_autobake_on,
        description='Bake this action on each export'
    )

    def autobake_effective(self, bobject):
        if not self.autobake_auto:
            return self.autobake_on
        if bobject.type == 'ARMATURE':
            for pbone in bobject.pose.bones:
                if pbone.constraints:
                    return True
        if bobject.constraints:
            return True
        return False

    autobake_custom_refine = bpy.props.BoolProperty(
        name='Custom Thresholds',
        description='Use custom thresholds for remove redundant keyframes'
    )
    autobake_refine_location = bpy.props.FloatProperty(
        default=0.001, min=0, soft_max=1,
        subtype='DISTANCE',
        description='Skip threshold for redundant location keyframes'
    )
    autobake_refine_rotation = bpy.props.FloatProperty(
        default=0.001, min=0, soft_max=1,
        subtype='ANGLE',
        description='Skip threshold for redundant rotation keyframes'
    )


class XRaySceneProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Scene
    export_root = bpy.props.StringProperty(
        name='Export Root',
        description='The root folder for export',
        subtype='DIR_PATH',
    )
    fmt_version = PropSDKVersion()
    object_export_motions = PropObjectMotionsExport()
    object_texture_name_from_image_path = PropObjectTextureNamesFromPath()
    materials_colorize_random_seed = bpy.props.IntProperty(min=0, max=255, options={'SKIP_SAVE'})
    materials_colorize_color_power = bpy.props.FloatProperty(
        default=0.5, min=0.0, max=1.0,
        options={'SKIP_SAVE'},
    )


__CLASSES__ = [
    XRayObjectProperties
    , XRayMeshProperties
    , XRayMaterialProperties
    , XRayArmatureProperties
    , XRayBoneProperties
    , XRayActionProperties
    , XRaySceneProperties
]


def register():
    for clas in __CLASSES__:
        registry.register_thing(clas, __name__)
        clas.b_type.xray = bpy.props.PointerProperty(type=clas)


def unregister():
    for clas in reversed(__CLASSES__):
        del clas.b_type.xray
        registry.unregister_thing(clas, __name__)
