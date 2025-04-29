# blender modules
import mathutils

# addon modules
from .. import fmt
from ... import motions
from .... import rw
from .... import utils


def write_ik_data(arm_obj, bones, scale, ogf_writer):
    ik_writer = rw.write.PackedWriter()
    mul = utils.version.get_multiply()

    for bone, obj in bones:
        xray = bone.xray

        # get types
        shape_type = utils.bone.get_bone_prop(xray.shape, 'type', 4)
        ik_type = utils.bone.get_bone_prop(xray.ikjoint, 'type', 6)

        # get shapes

        # box translation and half size
        box_trn = mathutils.Vector(xray.shape.box_trn) * scale
        box_hsz = mathutils.Vector(xray.shape.box_hsz) * scale

        # sphere position and radius
        sph_pos = mathutils.Vector(xray.shape.sph_pos) * scale
        sph_rad = xray.shape.sph_rad * scale

        # cylinder position, height, radius
        cyl_pos = mathutils.Vector(xray.shape.cyl_pos) * scale
        cyl_hgt = xray.shape.cyl_hgh * scale
        cyl_rad = xray.shape.cyl_rad * scale

        # get limits
        x_min, x_max = utils.bone.get_x_limits(xray.ikjoint)
        x_min, x_max = utils.bone.get_ode_ik_limits(x_min, x_max)
        y_min, y_max = utils.bone.get_ode_ik_limits(
            xray.ikjoint.lim_y_min,
            xray.ikjoint.lim_y_max
        )
        z_min, z_max = utils.bone.get_ode_ik_limits(
            xray.ikjoint.lim_z_min,
            xray.ikjoint.lim_z_max
        )

        # get center of mass
        cmass = mathutils.Vector(xray.mass.center) * scale

        # get bind pose matrix

        # bind pose matrix
        mat = mul(
            arm_obj.matrix_world,
            bone.matrix_local,
            motions.const.MATRIX_BONE_INVERTED
        )
        # parent bone
        par = utils.bone.find_bone_exportable_parent(bone)

        if par:
            # parent matrix
            pmat = mul(
                arm_obj.matrix_world,
                par.matrix_local,
                motions.const.MATRIX_BONE_INVERTED
            )
            # bind pose matrix
            mat = mul(pmat.inverted(), mat)

        # bind rotation
        euler = mat.to_euler('YXZ')
        euler.x = -euler.x
        euler.y = -euler.y
        euler.z = -euler.z

        # bind translation
        trn = mat.to_translation() * scale

        # write

        # header
        ik_writer.putf('<I', fmt.BONE_VERSION_1)
        ik_writer.puts(xray.gamemtl)
        ik_writer.putf('<2H', shape_type, xray.shape.flags)

        # shapes
        ik_writer.putf(
            '<27f',

            # box
            *xray.shape.box_rot,    # box rotate 3x3 matrix 9 float
            *box_trn,    # box translate 3 float
            *box_hsz,    # box half size 3 float

            # sphere
            *sph_pos,    # sphere position 3 float
            sph_rad,    # sphere radius 1 float

            # cylinder
            *cyl_pos,    # cylinder position 3 float
            *xray.shape.cyl_dir,    # cylinder direction 3 float
            cyl_hgt,    # cylinder height 1 float
            cyl_rad    # cylinder radius 1 float
        )

        # limits and others
        ik_writer.putf(
            '<I14fI3f',

            ik_type,

            # x limits
            x_min,
            x_max,
            xray.ikjoint.lim_x_spr,
            xray.ikjoint.lim_x_dmp,

            # y limits
            y_min,
            y_max,
            xray.ikjoint.lim_y_spr,
            xray.ikjoint.lim_y_dmp,

            # z limits
            z_min,
            z_max,
            xray.ikjoint.lim_z_spr,
            xray.ikjoint.lim_z_dmp,

            xray.ikjoint.spring,
            xray.ikjoint.damping,

            xray.ikflags,

            xray.breakf.force,
            xray.breakf.torque,
            xray.friction
        )

        # bind pose
        ik_writer.putv3f(euler)
        ik_writer.putv3f(trn)

        # mass
        ik_writer.putf('<f', xray.mass.value)
        ik_writer.putv3f(cmass)

    # write chunk
    ogf_writer.put(fmt.Chunks_v4.S_IKDATA_2, ik_writer)
