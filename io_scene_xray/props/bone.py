# standart modules
import math

# blender modules
import bpy
import mathutils
import gpu

# addon modules
from . import utility
from .. import viewport
from .. import ops
from .. import utils

if not utils.version.IS_34:
    import bgl


def _iszero(vector):
    return not any(vector)


class XRayShapeProps(bpy.types.PropertyGroup):
    _CURVER_DATA = 1

    version_data = bpy.props.IntProperty()

    # type
    type = bpy.props.EnumProperty(
        items=(
            ('0', 'None', ''),
            ('1', 'Box', ''),
            ('2', 'Sphere', ''),
            ('3', 'Cylinder', ''),
            ('4', 'Custom ', '')
        ),
        update=lambda self, context: ops.edit_helpers.bone_shape.HELPER.update(context),
    )
    type_custom_id = bpy.props.IntProperty(default=0, min=0)

    # flags
    flags = bpy.props.IntProperty()
    flags_nopickable = utility.gen_flag_prop(mask=0x1)
    flags_removeafterbreak = utility.gen_flag_prop(mask=0x2)
    flags_nophysics = utility.gen_flag_prop(mask=0x4)
    flags_nofogcollider = utility.gen_flag_prop(mask=0x8)

    # box
    box_rot = bpy.props.FloatVectorProperty(size=9)
    box_trn = bpy.props.FloatVectorProperty()
    box_hsz = bpy.props.FloatVectorProperty()

    # sphere
    sph_pos = bpy.props.FloatVectorProperty()
    sph_rad = bpy.props.FloatProperty()

    # cylinder
    cyl_pos = bpy.props.FloatVectorProperty()
    cyl_dir = bpy.props.FloatVectorProperty()
    cyl_hgh = bpy.props.FloatProperty()
    cyl_rad = bpy.props.FloatProperty()

    def check_version_different(self):
        ver = 0

        if self.version_data == self._CURVER_DATA:
            return ver

        if self.type == '0':    # none
            return ver

        elif self.type == '1':    # box
            if (
                _iszero(self.box_trn) and
                _iszero(self.box_rot) and
                _iszero(self.box_hsz)
            ):
                return ver    # default shape

        elif self.type == '2':    # sphere
            if (
                _iszero(self.sph_pos) and
                not self.sph_rad
            ):
                return ver    # default shape

        elif self.type == '3':    # cylinder
            if (
                _iszero(self.cyl_pos) and
                _iszero(self.cyl_dir) and
                not self.cyl_rad and
                not self.cyl_hgh
            ):
                return ver    # default shape

        elif self.type == '4':    # custom
            return ver

        if self.version_data < self._CURVER_DATA:
            ver = 1
        else:
            ver = 2

        return ver

    @staticmethod
    def fmt_version_different(res):
        if res == 1:
            ver = 'obsolete'
        elif res == 2:
            ver = 'newest'
        else:
            ver = 'different'
        return ver

    def set_curver(self):
        self.version_data = self._CURVER_DATA

    def get_matrix_basis(self) -> mathutils.Matrix:
        result = mathutils.Matrix.Identity(4)

        if self.type == '1':    # box
            scale = utils.version.multiply(
                mathutils.Matrix.Scale(self.box_hsz[0], 4, (1, 0, 0)),
                mathutils.Matrix.Scale(self.box_hsz[1], 4, (0, 1, 0)),
                mathutils.Matrix.Scale(self.box_hsz[2], 4, (0, 0, 1))
            )
            rot = self.box_rot
            rot_mat = mathutils.Matrix((rot[0:3], rot[3:6], rot[6:9]))
            result = utils.version.multiply(
                mathutils.Matrix.Translation(self.box_trn),
                rot_mat.transposed().to_4x4(),
                scale
            )

        elif self.type == '2':    # sphere
            pos = mathutils.Matrix.Translation(self.sph_pos)
            scale = utils.version.multiply(
                mathutils.Matrix.Scale(self.sph_rad, 4, (1, 0, 0)),
                mathutils.Matrix.Scale(self.sph_rad, 4, (0, 1, 0)),
                mathutils.Matrix.Scale(self.sph_rad, 4, (0, 0, 1))
            )
            result = utils.version.multiply(pos, scale)

        elif self.type == '3':    # cylinder
            v_dir = mathutils.Vector(self.cyl_dir)
            q_rot = v_dir.rotation_difference((0, 1, 0))
            scale = utils.version.multiply(
                mathutils.Matrix.Scale(self.cyl_rad, 4, (1, 0, 0)),
                mathutils.Matrix.Scale(self.cyl_hgh, 4, (0, 1, 0)),
                mathutils.Matrix.Scale(self.cyl_rad, 4, (0, 0, 1))
            )
            result = utils.version.multiply(
                mathutils.Matrix.Translation(self.cyl_pos),
                q_rot.to_matrix().transposed().to_4x4(),
                scale
            )

        return result


class XRayBreakProps(bpy.types.PropertyGroup):
    force = bpy.props.FloatProperty(min=0.0)
    torque = bpy.props.FloatProperty(min=0.0)


class XRayIKJointProps(bpy.types.PropertyGroup):
    # type
    type = bpy.props.EnumProperty(items=(
        ('4', 'None', ''),
        ('0', 'Rigid', ''),
        ('1', 'Cloth', ''),
        ('2', 'Joint', ''),
        ('3', 'Wheel ', ''),
        ('5', 'Slider ', ''),
        ('6', 'Custom ', '')
    ))
    type_custom_id = bpy.props.IntProperty(default=0, min=0)

    # x limits
    lim_x_min = bpy.props.FloatProperty(
        min=-math.pi,
        max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    )
    lim_x_max = bpy.props.FloatProperty(
        min=-math.pi,
        max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    )
    lim_x_spr = bpy.props.FloatProperty(min=0.0, max=1000.0)
    lim_x_dmp = bpy.props.FloatProperty(min=0.0, max=1000.0)

    # y limits
    lim_y_min = bpy.props.FloatProperty(
        min=-math.pi,
        max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    )
    lim_y_max = bpy.props.FloatProperty(
        min=-math.pi,
        max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    )
    lim_y_spr = bpy.props.FloatProperty(min=0.0, max=1000.0)
    lim_y_dmp = bpy.props.FloatProperty(min=0.0, max=1000.0)

    # z limits
    lim_z_min = bpy.props.FloatProperty(
        min=-math.pi, max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    )
    lim_z_max = bpy.props.FloatProperty(
        min=-math.pi, max=math.pi,
        update=ops.joint_limits.update_limit,
        subtype='ANGLE'
    )
    lim_z_spr = bpy.props.FloatProperty(min=0.0, max=1000.0)
    lim_z_dmp = bpy.props.FloatProperty(min=0.0, max=1000.0)

    # slide
    slide_min = bpy.props.FloatProperty(update=ops.joint_limits.update_slider)
    slide_max = bpy.props.FloatProperty(update=ops.joint_limits.update_slider)

    # others
    spring = bpy.props.FloatProperty(min=0.0, max=1000.0)
    damping = bpy.props.FloatProperty(min=0.0, max=1000.0)


class XRayMassProps(bpy.types.PropertyGroup):
    value = bpy.props.FloatProperty(name='Mass', precision=3, min=0.0)
    center = bpy.props.FloatVectorProperty(
        name='Center of Mass',
        precision=3
    )


def _set_ikflags_breakable(self, value):
    self.ikflags = self.ikflags | 0x1 if value else self.ikflags & ~0x1


class XRayBoneProps(bpy.types.PropertyGroup):
    b_type = bpy.types.Bone

    exportable = bpy.props.BoolProperty(
        name='Exportable',
        default=True,
        description='Enable Bone to be exported'
    )
    version = bpy.props.IntProperty()
    length = bpy.props.FloatProperty(name='Length')
    gamemtl = bpy.props.StringProperty(default='default_object')
    shape = bpy.props.PointerProperty(type=XRayShapeProps)
    ikflags = bpy.props.IntProperty()
    ikflags_breakable = bpy.props.BoolProperty(
        get=lambda self: self.ikflags & 0x1,
        set=_set_ikflags_breakable,
        options={'SKIP_SAVE'}
    )
    ikjoint = bpy.props.PointerProperty(type=XRayIKJointProps)
    breakf = bpy.props.PointerProperty(type=XRayBreakProps)
    friction = bpy.props.FloatProperty(min=0.0)
    mass = bpy.props.PointerProperty(type=XRayMassProps)


prop_groups = (
    XRayShapeProps,
    XRayBreakProps,
    XRayIKJointProps,
    XRayMassProps,
    XRayBoneProps
)


def register():
    utils.version.register_classes(prop_groups)


def unregister():
    utils.version.unregister_prop_groups(prop_groups)
