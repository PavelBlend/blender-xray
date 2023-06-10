# addon modules
from .. import obj
from ... import utils
from ... import log
from ... import rw


@log.with_context(name='bones-partitions')
def _export_partitions(context, bpy_obj):
    log.update(object=bpy_obj.name)
    packed_writer = rw.write.PackedWriter()
    groups_count = len(bpy_obj.pose.bone_groups)

    if not groups_count or not context.export_bone_parts:
        packed_writer.putf('<I', 0)
        return packed_writer

    exportable_bones = tuple(
        bone
        for bone in bpy_obj.pose.bones
            if utils.bone.is_exportable_bone(bpy_obj.data.bones[bone.name])
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
def _export_bone_data(bpy_obj, bone, scale):
    log.update(bone=bone.name)
    chunked_writer = rw.write.ChunkedWriter()
    chunks = obj.fmt.Chunks.Bone
    xray = bone.xray
    pose_bone = bpy_obj.pose.bones[bone.name]

    # name
    packed_writer = rw.write.PackedWriter()
    packed_writer.puts(bone.name)
    chunked_writer.put(chunks.DEF, packed_writer)

    # material
    packed_writer = rw.write.PackedWriter()
    packed_writer.puts(xray.gamemtl)
    chunked_writer.put(chunks.MATERIAL, packed_writer)

    # shape
    shape = xray.shape
    shape_type = utils.bone.get_bone_prop(shape, 'type', 4)
    packed_writer = rw.write.PackedWriter()
    packed_writer.putf('<2H', shape_type, shape.flags)

    # box shape
    box_trn = list(shape.box_trn)
    box_trn[0] *= scale.x
    box_trn[1] *= scale.y
    box_trn[2] *= scale.z

    box_hsz = list(shape.box_hsz)
    box_hsz[0] *= scale.x
    box_hsz[1] *= scale.y
    box_hsz[2] *= scale.z

    packed_writer.putf('<9f', *shape.box_rot)
    packed_writer.putf('<3f', *box_trn)
    packed_writer.putf('<3f', *box_hsz)

    # sphere shape
    sph_pos = list(shape.sph_pos)
    sph_pos[0] *= scale.x
    sph_pos[1] *= scale.y
    sph_pos[2] *= scale.z

    packed_writer.putf('<3f', *sph_pos)
    packed_writer.putf('<f', shape.sph_rad * scale.x)

    # cylinder shape
    cyl_pos = list(shape.cyl_pos)
    cyl_pos[0] *= scale.x
    cyl_pos[1] *= scale.y
    cyl_pos[2] *= scale.z

    packed_writer.putf('<3f', *cyl_pos)
    packed_writer.putf('<3f', *shape.cyl_dir)
    packed_writer.putf('<f', shape.cyl_hgh * scale.x)
    packed_writer.putf('<f', shape.cyl_rad * scale.x)

    chunked_writer.put(chunks.SHAPE, packed_writer)

    # ik flags
    if xray.ikflags:
        packed_writer = rw.write.PackedWriter()
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

    packed_writer = rw.write.PackedWriter()
    ik_type = utils.bone.get_bone_prop(ik, 'type', 6)
    packed_writer.putf('<I', ik_type)

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
        packed_writer = rw.write.PackedWriter()
        packed_writer.putf('<f', xray.breakf.force)
        packed_writer.putf('<f', xray.breakf.torque)
        chunked_writer.put(chunks.BREAK_PARAMS, packed_writer)

    # friction
    packed_writer = rw.write.PackedWriter()
    packed_writer.putf('<f', xray.friction)
    chunked_writer.put(chunks.FRICTION, packed_writer)

    # mass params
    cmass = list(xray.mass.center)
    cmass[0] *= scale.x
    cmass[1] *= scale.y
    cmass[2] *= scale.z

    packed_writer = rw.write.PackedWriter()
    packed_writer.putf('<f', xray.mass.value)
    packed_writer.putv3f(cmass)
    chunked_writer.put(chunks.MASS_PARAMS, packed_writer)

    return chunked_writer


@log.with_context(name='export-bones')
@utils.stats.timer
def export_file(context):
    utils.stats.status('Export File', context.filepath)

    arm_obj = context.bpy_arm_obj
    log.update(object=arm_obj.name)
    chunked_writer = rw.write.ChunkedWriter()

    # get armature scale
    root_obj = utils.obj.find_root(arm_obj)
    _, scale = utils.ie.get_obj_scale_matrix(root_obj, arm_obj)

    # export bones data
    bone_index = 0
    if context.export_bone_properties:
        for bone in arm_obj.data.bones:
            if not utils.bone.is_exportable_bone(bone):
                continue
            bone_chunked_writer = _export_bone_data(arm_obj, bone, scale)
            chunked_writer.put(bone_index, bone_chunked_writer)
            bone_index += 1

    # export partitions
    partitions_packed_writer = _export_partitions(context, arm_obj)
    chunked_writer.put(
        obj.fmt.Chunks.Object.PARTITIONS1,
        partitions_packed_writer
    )

    # save
    rw.utils.save_file(context.filepath, chunked_writer)
