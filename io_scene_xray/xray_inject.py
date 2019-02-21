import time
import math

import bgl
import bpy
import mathutils

from .plugin_prefs import PropObjectMotionsExport, PropObjectTextureNamesFromPath, PropSDKVersion
from .edit_helpers.bone_shape import HELPER as seh
from . import utils
from .details.types import (
    XRayObjectDetailsProperties,
    XRayObjectDetailsModelProperties,
    XRayObjectDetailsSlotsProperties,
    XRayObjectDetailsSlotsLightingProperties,
    XRayObjectDetailsSlotsMeshesProperties
    )
from . import registry
from .ops import joint_limits


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
    is_details = bpy.props.BoolProperty(default=False)
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

    motions = bpy.props.StringProperty(
        description='!Legacy: use \'motions_collection\' instead'
    )
    motions_collection = bpy.props.CollectionProperty(type=MotionRef)
    motions_collection_index = bpy.props.IntProperty(options={'SKIP_SAVE'})
    show_motions = bpy.props.BoolProperty(description='View motions', options={'SKIP_SAVE'})

    helper_data = bpy.props.StringProperty()
    export_path = bpy.props.StringProperty(
        name='Export Path',
        description='Path relative to the root export folder'
    )

    detail = bpy.props.PointerProperty(type=XRayObjectDetailsProperties)

    def initialize(self, context):
        if not self.version:
            if context.operation == 'LOADED':
                self.version = -1
            elif context.operation == 'CREATED':
                self.version = context.plugin_version_number
                self.root = context.thing.type == 'MESH'
                if context.thing.type == 'ARMATURE':
                    context.thing.data.xray.joint_limits_type = 'XRAY'


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
    joint_limit_type_items = (
        ('IK', 'IK Limits', ''),
        ('XRAY', 'X-Ray Limits', '')
    )
    joint_limits_type = bpy.props.EnumProperty(
        items=joint_limit_type_items, name='Export Limits From', default='IK'
    )
    display_bone_limits = bpy.props.BoolProperty(name='Display Bone Limits', default=False)
    display_bone_limits_radius = bpy.props.FloatProperty(name='Gizmo Radius', default=0.1, min=0.0)
    display_bone_limit_x = bpy.props.BoolProperty(name='Limit X', default=True)
    display_bone_limit_y = bpy.props.BoolProperty(name='Limit Y', default=True)
    display_bone_limit_z = bpy.props.BoolProperty(name='Limit Z', default=True)

    def check_different_version_bones(self):
        from functools import reduce
        return reduce(
            lambda x, y: x | y,
            [b.xray.shape.check_version_different() for b in self.id_data.bones],
            0,
        )


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

        type = bpy.props.EnumProperty(
            items=(
                ('0', 'None', ''),
                ('1', 'Box', ''),
                ('2', 'Sphere', ''),
                ('3', 'Cylinder', '')
            ),
            update=lambda self, ctx: seh.update(),
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

        def get_matrix_basis(self) -> mathutils.Matrix:
            typ = self.type
            if typ == '1':  # box
                rot = self.box_rot
                return mathutils.Matrix.Translation(self.box_trn) \
                    * mathutils.Matrix((rot[0:3], rot[3:6], rot[6:9])).transposed().to_4x4()
            if typ == '2':  # sphere
                return mathutils.Matrix.Translation(self.sph_pos)
            if typ == '3':  # cylinder
                v_dir = mathutils.Vector(self.cyl_dir)
                q_rot = v_dir.rotation_difference((0, 1, 0))
                return mathutils.Matrix.Translation(self.cyl_pos) \
                    * q_rot.to_matrix().transposed().to_4x4()

    class IKJointProperties(bpy.types.PropertyGroup):
        type = bpy.props.EnumProperty(items=(
            ('0', 'Rigid', ''),
            ('1', 'Cloth', ''),
            ('2', 'Joint', ''),
            ('3', 'Wheel', ''),
            ('4', 'None', ''),
            ('5', 'Slider', '')))

        lim_x_min = bpy.props.FloatProperty(
            min=-180.0, max=180, update=joint_limits.update_limit, subtype='ANGLE'
        )
        lim_x_max = bpy.props.FloatProperty(
            min=-180.0, max=180, update=joint_limits.update_limit, subtype='ANGLE'
        )
        lim_x_spr = bpy.props.FloatProperty()
        lim_x_dmp = bpy.props.FloatProperty()

        lim_y_min = bpy.props.FloatProperty(
            min=-180.0, max=180, update=joint_limits.update_limit, subtype='ANGLE'
        )
        lim_y_max = bpy.props.FloatProperty(
            min=-180.0, max=180, update=joint_limits.update_limit, subtype='ANGLE'
        )
        lim_y_spr = bpy.props.FloatProperty()
        lim_y_dmp = bpy.props.FloatProperty()

        lim_z_min = bpy.props.FloatProperty(
            min=-180.0, max=180, update=joint_limits.update_limit, subtype='ANGLE'
        )
        lim_z_max = bpy.props.FloatProperty(
            min=-180.0, max=180, update=joint_limits.update_limit, subtype='ANGLE'
        )
        lim_z_spr = bpy.props.FloatProperty()
        lim_z_dmp = bpy.props.FloatProperty()

        spring = bpy.props.FloatProperty()
        damping = bpy.props.FloatProperty()
        is_rigid = bpy.props.BoolProperty(get=lambda self: self.type == '0')

    class MassProperties(bpy.types.PropertyGroup):
        value = bpy.props.FloatProperty(name='Mass')
        center = bpy.props.FloatVectorProperty(name='Center of Mass')

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

    def ondraw_postview(self, obj_arm, bone):
        # draw limits
        arm_xray = obj_arm.data.xray
        if not obj_arm.hide and arm_xray.display_bone_limits and \
                        bone.xray.exportable and obj_arm.mode == 'POSE':
            if bone.select and bone.xray.ikjoint.type in {'2', '3', '5'} and \
                    bpy.context.object.name == obj_arm.name:

                from .gl_utils import draw_joint_limits, matrix_to_buffer

                bgl.glPushMatrix()
                bgl.glEnable(bgl.GL_BLEND)
                mat_translate = mathutils.Matrix.Translation(obj_arm.pose.bones[bone.name].matrix.to_translation())
                mat_rotate = obj_arm.data.bones[bone.name].matrix_local.to_euler().to_matrix().to_4x4()
                if bone.parent:
                    mat_rotate_parent = obj_arm.pose.bones[bone.parent.name].matrix_basis.to_euler().to_matrix().to_4x4()
                else:
                    mat_rotate_parent = mathutils.Matrix()

                mat = obj_arm.matrix_world * mat_translate * (mat_rotate * mat_rotate_parent) \
                    * mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
                bgl.glMultMatrixf(matrix_to_buffer(mat.transposed()))

                rotate = obj_arm.pose.bones[bone.name].rotation_euler

                ik = bone.xray.ikjoint

                if arm_xray.display_bone_limit_x:
                    draw_joint_limits(
                        math.degrees(rotate.x), ik.lim_x_min, ik.lim_x_max, 'X',
                        arm_xray.display_bone_limits_radius
                    )

                if arm_xray.display_bone_limit_y:
                    draw_joint_limits(
                        math.degrees(rotate.y), ik.lim_y_min, ik.lim_y_max, 'Y',
                        arm_xray.display_bone_limits_radius
                    )

                if arm_xray.display_bone_limit_z:
                    draw_joint_limits(
                        math.degrees(rotate.z), ik.lim_z_min, ik.lim_z_max, 'Z',
                        arm_xray.display_bone_limits_radius
                    )

                bgl.glPopMatrix()

        # draw shapes
        if obj_arm.hide or not obj_arm.data.xray.display_bone_shapes or \
                        not bone.xray.exportable or obj_arm.mode == 'EDIT':
            return

        if not obj_arm.name in bpy.context.scene.objects:
            return

        visible_armature_object = False
        for layer_index, layer in enumerate(obj_arm.layers):
            scene_layer = bpy.context.scene.layers[layer_index]
            if scene_layer and layer:
                visible_armature_object = True
                break

        if not visible_armature_object:
            return

        from .gl_utils import matrix_to_buffer, \
            draw_wire_cube, draw_wire_sphere, draw_wire_cylinder, draw_cross

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
            mat = obj_arm.matrix_world * obj_arm.pose.bones[bone.name].matrix \
                * mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
            bmat = mat
            bgl.glLineWidth(2)
            mat *= shape.get_matrix_basis()
            bgl.glMultMatrixf(matrix_to_buffer(mat.transposed()))
            if shape.type == '1':  # box
                draw_wire_cube(*shape.box_hsz)
            if shape.type == '2':  # sphere
                draw_wire_sphere(shape.sph_rad, 16)
            if shape.type == '3':  # cylinder
                draw_wire_cylinder(shape.cyl_rad, shape.cyl_hgh * 0.5, 16)
            bgl.glPopMatrix()
            bgl.glPushMatrix()
            ctr = self.mass.center
            trn = bmat * mathutils.Vector((ctr[0], ctr[2], ctr[1]))
            bgl.glTranslatef(*trn)
            draw_cross(0.05)
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


@registry.requires('ImportSkls')
class XRaySceneProperties(bpy.types.PropertyGroup):
    class ImportSkls(bpy.types.PropertyGroup):
        motion_index = bpy.props.IntProperty()

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
    import_skls = bpy.props.PointerProperty(type=ImportSkls)


__SUBCLASSES__ = [
    XRayObjectDetailsProperties,
    XRayObjectDetailsModelProperties,
    XRayObjectDetailsSlotsProperties,
    XRayObjectDetailsSlotsLightingProperties,
    XRayObjectDetailsSlotsMeshesProperties
    ]

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
    for subclass in reversed(__SUBCLASSES__):
        registry.register_thing(subclass, __name__)
    for clas in __CLASSES__:
        registry.register_thing(clas, __name__)
        clas.b_type.xray = bpy.props.PointerProperty(type=clas)


def unregister():
    for clas in reversed(__CLASSES__):
        del clas.b_type.xray
        registry.unregister_thing(clas, __name__)
    for subclass in __SUBCLASSES__:
        registry.unregister_thing(subclass, __name__)
