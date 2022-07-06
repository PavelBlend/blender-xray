# addon modules
from .. import utils
from .. import log
from .. import xray_io
from .. import obj


@log.with_context(name='bones-partitions')
def _export_partitions(context, bpy_obj):
    log.update(object=bpy_obj.name)
    packed_writer = xray_io.PackedWriter()
    groups_count = len(bpy_obj.pose.bone_groups)
    if not groups_count or not context.export_bone_parts:
        packed_writer.putf('<I', 0)
        return packed_writer
    exportable_bones = tuple(
        bone
        for bone in bpy_obj.pose.bones
            if utils.is_exportable_bone(bpy_obj.data.bones[bone.name])
    )
    all_groups = (
        (
            group.name,
            tuple(
                bone.name
                for bone in exportable_bones
                    if bone.bone_group == group
            )
        )
        for group in bpy_obj.pose.bone_groups
    )
    non_empty_groups = tuple(
        group
        for group in all_groups
            if group[1]
    )
    if non_empty_groups:
        packed_writer.putf('<I', len(non_empty_groups))
        for group_name, bones_names in non_empty_groups:
            packed_writer.puts(group_name)
            packed_writer.putf('<I', len(bones_names))
            for bone_name in bones_names:
                packed_writer.puts(bone_name)
    else:
        packed_writer.putf('<I', 0)
    return packed_writer


@log.with_context(name='bone-properties')
def _export_bone_data(bpy_obj, bone):
    log.update(bone=bone.name)
    chunked_writer = xray_io.ChunkedWriter()
    chunks = obj.fmt.Chunks.Bone
    xray = bone.xray
    pose_bone = bpy_obj.pose.bones[bone.name]
    # name
    packed_writer = xray_io.PackedWriter()
    packed_writer.puts(bone.name)
    chunked_writer.put(chunks.DEF, packed_writer)
    # material
    packed_writer = xray_io.PackedWriter()
    packed_writer.puts(xray.gamemtl)
    chunked_writer.put(chunks.MATERIAL, packed_writer)
    # shape
    shape = xray.shape
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<H', int(shape.type))
    packed_writer.putf('<H', shape.flags)
    packed_writer.putf('<9f', *shape.box_rot)
    packed_writer.putf('<3f', *shape.box_trn)
    packed_writer.putf('<3f', *shape.box_hsz)
    packed_writer.putf('<3f', *shape.sph_pos)
    packed_writer.putf('<f', shape.sph_rad)
    packed_writer.putf('<3f', *shape.cyl_pos)
    packed_writer.putf('<3f', *shape.cyl_dir)
    packed_writer.putf('<f', shape.cyl_hgh)
    packed_writer.putf('<f', shape.cyl_rad)
    chunked_writer.put(chunks.SHAPE, packed_writer)
    # ik flags
    if xray.ikflags:
        packed_writer = xray_io.PackedWriter()
        packed_writer.putf('<I', xray.ikflags)
        chunked_writer.put(chunks.IK_FLAGS, packed_writer)
    # ik joint
    ik = xray.ikjoint
    if bpy_obj.data.xray.joint_limits_type == 'XRAY':
        # x limits
        x_min = ik.lim_x_min
        x_max = ik.lim_x_max
        # y limits
        y_min = ik.lim_y_min
        y_max = ik.lim_y_max
        # z limits
        z_min = ik.lim_z_min
        z_max = ik.lim_z_max
    else:
        # x limits
        x_min = pose_bone.ik_min_x
        x_max = pose_bone.ik_max_x
        # y limits
        y_min = pose_bone.ik_min_y
        y_max = pose_bone.ik_max_y
        # z limits
        z_min = pose_bone.ik_min_z
        z_max = pose_bone.ik_max_z
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', int(ik.type))
    # write limit x
    packed_writer.putf('<2f', x_min, x_max)
    packed_writer.putf('<2f', ik.lim_x_spr, ik.lim_x_dmp)
    # write limit y
    packed_writer.putf('<2f', y_min, y_max)
    packed_writer.putf('<2f', ik.lim_y_spr, ik.lim_y_dmp)
    # write limit z
    packed_writer.putf('<2f', z_min, z_max)
    packed_writer.putf('<2f', ik.lim_z_spr, ik.lim_z_dmp)
    # spring and damping
    packed_writer.putf('<2f', ik.spring, ik.damping)
    chunked_writer.put(chunks.IK_JOINT, packed_writer)
    # break params
    if xray.ikflags_breakable:
        packed_writer = xray_io.PackedWriter()
        packed_writer.putf('<f', xray.breakf.force)
        packed_writer.putf('<f', xray.breakf.torque)
        chunked_writer.put(chunks.BREAK_PARAMS, packed_writer)
    # friction
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<f', xray.friction)
    chunked_writer.put(chunks.FRICTION, packed_writer)
    # mass params
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<f', xray.mass.value)
    packed_writer.putv3f(xray.mass.center)
    chunked_writer.put(chunks.MASS_PARAMS, packed_writer)
    return chunked_writer


@log.with_context(name='export-bones')
def export_file(context):
    bpy_obj = context.bpy_arm_obj
    log.update(object=bpy_obj.name)
    chunked_writer = xray_io.ChunkedWriter()
    bone_index = 0
    if context.export_bone_properties:
        for bone in bpy_obj.data.bones:
            if not utils.is_exportable_bone(bone):
                continue
            bone_chunked_writer = _export_bone_data(bpy_obj, bone)
            chunked_writer.put(bone_index, bone_chunked_writer)
            bone_index += 1
    partitions_packed_writer = _export_partitions(context, bpy_obj)
    chunked_writer.put(
        obj.fmt.Chunks.Object.PARTITIONS1,
        partitions_packed_writer
    )
    utils.save_file(context.filepath, chunked_writer)
