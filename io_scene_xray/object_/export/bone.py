
from ... import xray_io
from ... import log
from ... import utils
from ... import xray_motions
from .. import format_
from . import main


def export_bone(bpy_arm_obj, bpy_root, bpy_bone, writers, bonemap, context):
    real_parent = utils.find_bone_exportable_parent(bpy_bone)
    if real_parent:
        if bonemap.get(real_parent) is None:
            export_bone(
                bpy_arm_obj, bpy_root, real_parent, writers, bonemap, context
            )

    xray = bpy_bone.xray
    writer = xray_io.ChunkedWriter()
    writers.append(writer)
    bonemap[bpy_bone] = writer
    writer.put(
        format_.Chunks.Bone.VERSION, xray_io.PackedWriter().putf('H', 0x02)
    )
    writer.put(format_.Chunks.Bone.DEF, xray_io.PackedWriter()
               .puts(bpy_bone.name)
               .puts(real_parent.name if real_parent else '')
               .puts(bpy_bone.name))  # vmap
    xmat = bpy_root.matrix_world.inverted() * bpy_arm_obj.matrix_world
    mat = xmat * bpy_bone.matrix_local * xray_motions.MATRIX_BONE_INVERTED
    if real_parent:
        mat = (xmat * real_parent.matrix_local * \
            xray_motions.MATRIX_BONE_INVERTED).inverted() * mat
    eul = mat.to_euler('YXZ')
    writer.put(format_.Chunks.Bone.BIND_POSE, xray_io.PackedWriter()
               .putf('fff', *main.pw_v3f(mat.to_translation()))
               .putf('fff', -eul.x, -eul.z, -eul.y)
               .putf('f', xray.length))
    writer.put(
        format_.Chunks.Bone.MATERIAL, xray_io.PackedWriter().puts(xray.gamemtl)
    )
    verdif = xray.shape.check_version_different()
    if verdif != 0:
        log.warn(
            'bone edited with a different version of this plugin',
            bone=bpy_bone.name,
            version=xray.shape.fmt_version_different(verdif)
        )
    writer.put(format_.Chunks.Bone.SHAPE, xray_io.PackedWriter()
               .putf('H', int(xray.shape.type))
               .putf('H', xray.shape.flags)
               .putf('fffffffff', *xray.shape.box_rot)
               .putf('fff', *xray.shape.box_trn)
               .putf('fff', *xray.shape.box_hsz)
               .putf('fff', *xray.shape.sph_pos)
               .putf('f', xray.shape.sph_rad)
               .putf('fff', *xray.shape.cyl_pos)
               .putf('fff', *xray.shape.cyl_dir)
               .putf('f', xray.shape.cyl_hgh)
               .putf('f', xray.shape.cyl_rad))
    pose_bone = bpy_arm_obj.pose.bones[bpy_bone.name]
    ik = xray.ikjoint
    if bpy_arm_obj.data.xray.joint_limits_type == 'XRAY':
        writer.put(format_.Chunks.Bone.IK_JOINT, xray_io.PackedWriter()
                .putf('I', int(ik.type))
                .putf('ff', ik.lim_x_min, ik.lim_x_max)
                .putf('ff', ik.lim_x_spr, ik.lim_x_dmp)
                .putf('ff', ik.lim_y_min, ik.lim_y_max)
                .putf('ff', ik.lim_y_spr, ik.lim_y_dmp)
                .putf('ff', ik.lim_z_min, ik.lim_z_max)
                .putf('ff', ik.lim_z_spr, ik.lim_z_dmp)
                .putf('ff', ik.spring, ik.damping))
    else:
        writer.put(format_.Chunks.Bone.IK_JOINT, xray_io.PackedWriter()
                .putf('I', int(ik.type))
                .putf('ff', pose_bone.ik_min_x, pose_bone.ik_max_x)
                .putf('ff', ik.lim_x_spr, ik.lim_x_dmp)
                .putf('ff', pose_bone.ik_min_y, pose_bone.ik_max_y)
                .putf('ff', ik.lim_y_spr, ik.lim_y_dmp)
                .putf('ff', pose_bone.ik_min_z, pose_bone.ik_max_z)
                .putf('ff', ik.lim_z_spr, ik.lim_z_dmp)
                .putf('ff', ik.spring, ik.damping))
    if xray.ikflags:
        writer.put(
            format_.Chunks.Bone.IK_FLAGS,
            xray_io.PackedWriter().putf('I', xray.ikflags)
        )
        if xray.ikflags_breakable:
            writer.put(format_.Chunks.Bone.BREAK_PARAMS, xray_io.PackedWriter()
                       .putf('f', xray.breakf.force)
                       .putf('f', xray.breakf.torque))
    if int(ik.type) and xray.friction:
        writer.put(format_.Chunks.Bone.FRICTION, xray_io.PackedWriter()
                   .putf('f', xray.friction))
    if xray.mass.value:
        writer.put(format_.Chunks.Bone.MASS_PARAMS, xray_io.PackedWriter()
                   .putf('f', xray.mass.value)
                   .putf('fff', *main.pw_v3f(xray.mass.center)))
