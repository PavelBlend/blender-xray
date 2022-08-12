# addon modules
from . import main
from .. import fmt
from ... import text
from ... import xray_io
from ... import log
from ... import utils
from ... import motions


def export_bone(
        bpy_arm_obj,
        bpy_bone,
        writers,
        bonemap,
        edit_mode_matrices,
        multiply
    ):

    # export parent bone
    real_parent = utils.find_bone_exportable_parent(bpy_bone)
    if real_parent:
        if bonemap.get(real_parent) is None:
            export_bone(
                bpy_arm_obj,
                real_parent,
                writers,
                bonemap,
                edit_mode_matrices,
                multiply
            )

    xray = bpy_bone.xray
    writer = xray_io.ChunkedWriter()
    writers.append(writer)
    bonemap[bpy_bone] = writer

    # version chunk
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<H', fmt.CURRENT_BONE_VERSION)
    writer.put(fmt.Chunks.Bone.VERSION, packed_writer)

    # check bone name
    bone_name = bpy_bone.name.lower()
    if bone_name != bpy_bone.name:
        log.warn(
            text.warn.object_bone_uppercase,
            old=bpy_bone.name,
            new=bone_name
        )

    # def chunk
    packed_writer = xray_io.PackedWriter()
    packed_writer.puts(bone_name)
    packed_writer.puts(real_parent.name if real_parent else '')
    packed_writer.puts(bone_name)    # vmap
    writer.put(fmt.Chunks.Bone.DEF, packed_writer)

    # calculate bone matrix
    edit_mode_matrix = edit_mode_matrices[bpy_bone.name]
    matrix = edit_mode_matrix
    if real_parent:
        parent_matrix = edit_mode_matrices[real_parent.name]
        matrix = multiply(
            multiply(
                parent_matrix,
                motions.const.MATRIX_BONE_INVERTED
            ).inverted(),
            edit_mode_matrix
        )
    matrix = multiply(matrix, motions.const.MATRIX_BONE_INVERTED)
    euler = matrix.to_euler('YXZ')

    # bind pose chunk
    packed_writer = xray_io.PackedWriter()
    packed_writer.putv3f(matrix.to_translation())
    packed_writer.putf('<3f', -euler.x, -euler.z, -euler.y)
    packed_writer.putf('<f', xray.length)
    writer.put(fmt.Chunks.Bone.BIND_POSE, packed_writer)

    # material chunk
    packed_writer = xray_io.PackedWriter()
    packed_writer.puts(xray.gamemtl)
    writer.put(fmt.Chunks.Bone.MATERIAL, packed_writer)

    # check shape version
    verdif = xray.shape.check_version_different()
    if verdif != 0:
        log.warn(
            text.warn.object_bone_plugin_ver,
            bone=bpy_bone.name,
            version=xray.shape.fmt_version_different(verdif)
        )

    # shape chunk
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<H', int(xray.shape.type))
    packed_writer.putf('<H', xray.shape.flags)
    packed_writer.putf('<9f', *xray.shape.box_rot)
    packed_writer.putf('<3f', *xray.shape.box_trn)
    packed_writer.putf('<3f', *xray.shape.box_hsz)
    packed_writer.putf('<3f', *xray.shape.sph_pos)
    packed_writer.putf('<f', xray.shape.sph_rad)
    packed_writer.putf('<3f', *xray.shape.cyl_pos)
    packed_writer.putf('<3f', *xray.shape.cyl_dir)
    packed_writer.putf('<f', xray.shape.cyl_hgh)
    packed_writer.putf('<f', xray.shape.cyl_rad)
    writer.put(fmt.Chunks.Bone.SHAPE, packed_writer)

    # ik joint chunk
    ik = xray.ikjoint
    if bpy_arm_obj.data.xray.joint_limits_type == 'XRAY':
        lim_x_min = ik.lim_x_min
        lim_x_max = ik.lim_x_max
        lim_y_min = ik.lim_y_min
        lim_y_max = ik.lim_y_max
        lim_z_min = ik.lim_z_min
        lim_z_max = ik.lim_z_max
    else:
        pose_bone = bpy_arm_obj.pose.bones[bpy_bone.name]
        lim_x_min = pose_bone.ik_min_x
        lim_x_max = pose_bone.ik_max_x
        lim_y_min = pose_bone.ik_min_y
        lim_y_max = pose_bone.ik_max_y
        lim_z_min = pose_bone.ik_min_z
        lim_z_max = pose_bone.ik_max_z
    packed_writer = xray_io.PackedWriter()
    ik_type = int(ik.type)
    packed_writer.putf('<I', ik_type)
    packed_writer.putf('<2f', lim_x_min, lim_x_max)
    packed_writer.putf('<2f', ik.lim_x_spr, ik.lim_x_dmp)
    packed_writer.putf('<2f', lim_y_min, lim_y_max)
    packed_writer.putf('<2f', ik.lim_y_spr, ik.lim_y_dmp)
    packed_writer.putf('<2f', lim_z_min, lim_z_max)
    packed_writer.putf('<2f', ik.lim_z_spr, ik.lim_z_dmp)
    packed_writer.putf('<2f', ik.spring, ik.damping)
    writer.put(fmt.Chunks.Bone.IK_JOINT, packed_writer)

    # ik flags chunk
    if xray.ikflags:
        packed_writer = xray_io.PackedWriter()
        packed_writer.putf('<I', xray.ikflags)
        writer.put(fmt.Chunks.Bone.IK_FLAGS, packed_writer)

        # break params chunk
        if xray.ikflags_breakable:
            packed_writer = xray_io.PackedWriter()
            packed_writer.putf('<f', xray.breakf.force)
            packed_writer.putf('<f', xray.breakf.torque)
            writer.put(fmt.Chunks.Bone.BREAK_PARAMS, packed_writer)

    # friction chunk
    if ik_type and xray.friction:
        packed_writer = xray_io.PackedWriter()
        packed_writer.putf('<f', xray.friction)
        writer.put(fmt.Chunks.Bone.FRICTION, packed_writer)

    # mass chunk
    if xray.mass.value:
        packed_writer = xray_io.PackedWriter()
        packed_writer.putf('<f', xray.mass.value)
        packed_writer.putv3f(xray.mass.center)
        writer.put(fmt.Chunks.Bone.MASS_PARAMS, packed_writer)
