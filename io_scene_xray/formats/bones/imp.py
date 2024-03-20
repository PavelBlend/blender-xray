# blender modules
import bpy

# addon modules
from .. import obj
from ... import log
from ... import text
from ... import utils
from ... import rw


@log.with_context(name='bones-partitions')
def _import_partitions(import_context, data, arm_obj, bpy_bones):
    packed_reader = rw.read.PackedReader(data)

    partitions_count = packed_reader.uint32()
    if not partitions_count:
        log.warn(
            text.warn.bones_not_have_boneparts,
            file=import_context.filepath
        )

    current_mode = arm_obj.mode
    pose = arm_obj.pose
    bpy.ops.object.mode_set(mode='POSE')

    try:
        for partition_id in range(partitions_count):
            name = packed_reader.gets()
            log.update(partition=name)

            bone_group = pose.bone_groups.get(name, None)
            if not bone_group:
                bpy.ops.pose.group_add()
                bone_group = pose.bone_groups.active
                bone_group.name = name

            bones_count = packed_reader.uint32()

            for bone_id in range(bones_count):
                bone_name = packed_reader.gets()
                bpy_bone = bpy_bones.get(bone_name, None)

                if bpy_bone:
                    pose.bones[bone_name].bone_group = bone_group
                else:
                    log.warn(
                        text.warn.bones_missing_bone,
                        partition=name,
                        bone=bone_name
                    )

    finally:
        bpy.ops.object.mode_set(mode=current_mode)


@log.with_context(name='bone-properties')
def _import_bone_data(data, arm_obj_name, bpy_bones):
    chunked_reader = rw.read.ChunkedReader(data)
    chunks = obj.fmt.Chunks.Bone

    # bone name
    packed_reader = rw.read.PackedReader(chunked_reader.next(chunks.DEF))
    name = packed_reader.gets().lower()
    log.update(bone=name)

    bpy_bone = bpy_bones.get(name, None)
    if not bpy_bone:
        log.warn(
            text.warn.bones_has_no_bone,
            armature_object=arm_obj_name,
            bone=name
        )
        return

    xray = bpy_bone.xray

    for chunk_id, chunk_data in chunked_reader:
        packed_reader = rw.read.PackedReader(chunk_data)

        if chunk_id == chunks.MATERIAL:
            xray.gamemtl = packed_reader.gets()

        elif chunk_id == chunks.SHAPE:
            shape_type = packed_reader.getf('<H')[0]
            utils.bone.safe_assign_enum_property(
                bpy_bone.name,
                xray.shape,
                'type',
                shape_type,
                text.get_tip(text.warn.ogf_bad_shape),
                4
            )

            xray.shape.flags = packed_reader.getf('<H')[0]

            # box shape
            xray.shape.box_rot = packed_reader.getf('<9f')
            xray.shape.box_trn = packed_reader.getf('<3f')
            xray.shape.box_hsz = packed_reader.getf('<3f')

            # sphere shape
            xray.shape.sph_pos = packed_reader.getf('<3f')
            xray.shape.sph_rad = packed_reader.getf('<f')[0]

            # cylinder shape
            xray.shape.cyl_pos = packed_reader.getf('<3f')
            xray.shape.cyl_dir = packed_reader.getf('<3f')
            xray.shape.cyl_hgh = packed_reader.getf('<f')[0]
            xray.shape.cyl_rad = packed_reader.getf('<f')[0]

            xray.shape.set_curver()

        elif chunk_id == chunks.IK_JOINT:
            ik = xray.ikjoint

            joint_type = packed_reader.uint32()
            utils.bone.safe_assign_enum_property(
                bpy_bone.name,
                ik,
                'type',
                joint_type,
                text.get_tip(text.warn.ogf_bad_joint),
                6
            )

            # limit x
            limit_min, limit_max = packed_reader.getf('<2f')
            utils.bone.set_x_limits(ik, limit_min, limit_max)
            ik.lim_x_spr, ik.lim_x_dmp = packed_reader.getf('<2f')

            # limit y
            ik.lim_y_min, ik.lim_y_max = packed_reader.getf('<2f')
            ik.lim_y_spr, ik.lim_y_dmp = packed_reader.getf('<2f')

            # limit z
            ik.lim_z_min, ik.lim_z_max = packed_reader.getf('<2f')
            ik.lim_z_spr, ik.lim_z_dmp = packed_reader.getf('<2f')

            # spring and damping
            ik.spring = packed_reader.getf('<f')[0]
            ik.damping = packed_reader.getf('<f')[0]

        elif chunk_id == chunks.MASS_PARAMS:
            xray.mass.value = packed_reader.getf('<f')[0]
            xray.mass.center = packed_reader.getv3fp()

        elif chunk_id == chunks.IK_FLAGS:
            xray.ikflags = packed_reader.uint32()

        elif chunk_id == chunks.BREAK_PARAMS:
            xray.breakf.force = packed_reader.getf('<f')[0]
            xray.breakf.torque = packed_reader.getf('<f')[0]

        elif chunk_id == chunks.FRICTION:
            xray.friction = packed_reader.getf('<f')[0]

        else:
            log.debug('unknown *.bones chunk', chunk_id=chunk_id)


def _import_main(chunked_reader, import_context):
    arm_obj = import_context.bpy_arm_obj

    bpy_bones = {
        bpy_bone.name.lower(): bpy_bone
        for bpy_bone in arm_obj.data.bones
    }

    for chunk_id, chunk_data in chunked_reader:

        # import partitions
        if chunk_id == obj.fmt.Chunks.Object.PARTITIONS1:
            if import_context.import_bone_parts:
                _import_partitions(
                    import_context,
                    chunk_data,
                    arm_obj,
                    bpy_bones
                )

        # import bone properties
        else:
            if import_context.import_bone_properties:
                _import_bone_data(chunk_data, arm_obj.name, bpy_bones)


@log.with_context(name='import-bones')
@utils.stats.timer
def import_file(imp_context):
    utils.stats.status('Import File', imp_context.filepath)

    reader = rw.utils.get_file_reader(imp_context.filepath, chunked=True)
    _import_main(reader, imp_context)
