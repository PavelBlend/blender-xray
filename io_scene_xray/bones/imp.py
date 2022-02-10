# blender modules
import bpy

# addon modules
from .. import log
from .. import text
from .. import utils
from .. import xray_io
from .. import ie_utils
from .. import obj


@log.with_context(name='import-bones-partitions')
def _import_partitions(import_context, data, arm_obj, bpy_bones):
    packed_reader = xray_io.PackedReader(data)
    partitions_count = packed_reader.int()
    if not partitions_count:
        log.warn(
            text.warn.bones_not_have_boneparts,
            file=import_context.filepath
        )
    current_mode = arm_obj.mode
    bpy.ops.object.mode_set(mode='POSE')
    try:
        for partition_id in range(partitions_count):
            name = packed_reader.gets()
            bone_group = arm_obj.pose.bone_groups.get(name, None)
            if not bone_group:
                bpy.ops.pose.group_add()
                bone_group = arm_obj.pose.bone_groups.active
                bone_group.name = name
            bones_count = packed_reader.int()
            for bone_id in range(bones_count):
                bone_name = packed_reader.gets()
                bpy_bone = bpy_bones.get(bone_name, None)
                if not bpy_bone:
                    log.warn(
                        text.warn.bones_missing_bone,
                        partition=name,
                        bone=bone_name
                    )
                else:
                    arm_obj.pose.bones[bone_name].bone_group = bone_group
    finally:
        bpy.ops.object.mode_set(mode=current_mode)


@log.with_context(name='import-bone-properties')
def _import_bone_data(data, arm_obj_name, bpy_bones, bone_index):
    chunked_reader = xray_io.ChunkedReader(data)
    chunks = obj.fmt.Chunks.Bone
    # bone name
    packed_reader = xray_io.PackedReader(chunked_reader.next(chunks.DEF))
    name = packed_reader.gets().lower()
    log.update(name=name)
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
        packed_reader = xray_io.PackedReader(chunk_data)
        if chunk_id == chunks.MATERIAL:
            xray.gamemtl = packed_reader.gets()
        elif chunk_id == chunks.SHAPE:
            shape_type = packed_reader.getf('<H')[0]
            obj.imp.bone.safe_assign_enum_property(
                xray.shape,
                'type',
                str(shape_type),
                'bone shape'
            )
            xray.shape.flags = packed_reader.getf('<H')[0]
            xray.shape.box_rot = packed_reader.getf('<9f')
            xray.shape.box_trn = packed_reader.getf('<3f')
            xray.shape.box_hsz = packed_reader.getf('<3f')
            xray.shape.sph_pos = packed_reader.getf('<3f')
            xray.shape.sph_rad = packed_reader.getf('<f')[0]
            xray.shape.cyl_pos = packed_reader.getf('<3f')
            xray.shape.cyl_dir = packed_reader.getf('<3f')
            xray.shape.cyl_hgh = packed_reader.getf('<f')[0]
            xray.shape.cyl_rad = packed_reader.getf('<f')[0]
            xray.shape.set_curver()
        elif chunk_id == chunks.IK_JOINT:
            ik = xray.ikjoint
            joint_type = str(packed_reader.int())
            obj.imp.bone.safe_assign_enum_property(
                ik,
                'type',
                joint_type,
                'bone ikjoint'
            )
            # limit x
            ik.lim_x_min, ik.lim_x_max = packed_reader.getf('<2f')
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
            xray.ikflags = packed_reader.int()
        elif chunk_id == chunks.BREAK_PARAMS:
            xray.breakf.force = packed_reader.getf('<f')[0]
            xray.breakf.torque = packed_reader.getf('<f')[0]
        elif chunk_id == chunks.FRICTION:
            xray.friction = packed_reader.getf('<f')[0]
        else:
            log.debug('unknown chunk', chunk_id=chunk_id)


def _import_main(data, import_context):
    chunked_reader = xray_io.ChunkedReader(data)
    chunks = obj.fmt.Chunks.Object
    arm_obj = import_context.bpy_arm_obj
    bpy_bones = {}
    for bpy_bone in arm_obj.data.bones:
        bpy_bones[bpy_bone.name.lower()] = bpy_bone
    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == chunks.PARTITIONS1:
            if import_context.import_bone_parts:
                _import_partitions(import_context, chunk_data, arm_obj, bpy_bones)
        else:
            if not import_context.import_bone_properties:
                continue
            bone_index = chunk_id
            _import_bone_data(chunk_data, arm_obj.name, bpy_bones, bone_index)


@log.with_context(name='import-bones')
def import_file(import_context):
    log.update(file=import_context.filepath)
    ie_utils.check_file_exists(import_context.filepath)
    data = utils.read_file(import_context.filepath)
    _import_main(data, import_context)
