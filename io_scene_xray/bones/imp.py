# blender modules
import bpy

# addon modules
from .. import utils, xray_io, log
from ..obj import fmt
from ..obj.imp.main import read_v3f
from ..obj.imp import bone as imp_bone


@log.with_context(name='bone')
def _import_bone_data(data, arm_obj_name, bpy_bones, bone_index):
    chunked_reader = xray_io.ChunkedReader(data)
    chunks = fmt.Chunks.Bone
    # bone name
    packed_reader = xray_io.PackedReader(chunked_reader.next(chunks.DEF))
    name = packed_reader.gets().lower()
    log.update(name=name)
    bpy_bone = bpy_bones.get(name, None)
    if not bpy_bone:
        log.warn(
            'Armature object "{}" has no bone'.format(arm_obj_name),
            bone=name
        )
        return
    xray = bpy_bone.xray
    for chunk_id, chunk_data in chunked_reader:
        packed_reader = xray_io.PackedReader(chunk_data)
        if chunk_id == chunks.MATERIAL:
            xray.gamemtl = packed_reader.gets()
        elif chunk_id == chunks.SHAPE:
            shape_type = packed_reader.getf('H')[0]
            imp_bone._safe_assign_enum_property(
                xray.shape,
                'type',
                str(shape_type),
                'bone shape'
            )
            xray.shape.flags = packed_reader.getf('H')[0]
            xray.shape.box_rot = packed_reader.getf('fffffffff')
            xray.shape.box_trn = packed_reader.getf('fff')
            xray.shape.box_hsz = packed_reader.getf('fff')
            xray.shape.sph_pos = packed_reader.getf('fff')
            xray.shape.sph_rad = packed_reader.getf('f')[0]
            xray.shape.cyl_pos = packed_reader.getf('fff')
            xray.shape.cyl_dir = packed_reader.getf('fff')
            xray.shape.cyl_hgh = packed_reader.getf('f')[0]
            xray.shape.cyl_rad = packed_reader.getf('f')[0]
            xray.shape.set_curver()
        elif chunk_id == chunks.IK_JOINT:
            ik = xray.ikjoint
            joint_type = str(packed_reader.int())
            imp_bone._safe_assign_enum_property(
                ik, 'type', joint_type, 'bone ikjoint'
            )
            # limit x
            ik.lim_x_min, ik.lim_x_max = packed_reader.getf('ff')
            ik.lim_x_spr, ik.lim_x_dmp = packed_reader.getf('ff')
            # limit y
            ik.lim_y_min, ik.lim_y_max = packed_reader.getf('ff')
            ik.lim_y_spr, ik.lim_y_dmp = packed_reader.getf('ff')
            # limit z
            ik.lim_z_min, ik.lim_z_max = packed_reader.getf('ff')
            ik.lim_z_spr, ik.lim_z_dmp = packed_reader.getf('ff')
            # spring and damping
            ik.spring = packed_reader.getf('f')[0]
            ik.damping = packed_reader.getf('f')[0]
        elif chunk_id == chunks.MASS_PARAMS:
            xray.mass.value = packed_reader.getf('f')[0]
            xray.mass.center = read_v3f(packed_reader)
        elif chunk_id == chunks.IK_FLAGS:
            xray.ikflags = packed_reader.int()
        elif chunk_id == chunks.BREAK_PARAMS:
            xray.breakf.force = packed_reader.getf('f')[0]
            xray.breakf.torque = packed_reader.getf('f')[0]
        elif chunk_id == chunks.FRICTION:
            xray.friction = packed_reader.getf('f')[0]
        else:
            log.debug('unknown chunk', chunk_id=chunk_id)


def _import_main(data):
    chunked_reader = xray_io.ChunkedReader(data)
    chunks = fmt.Chunks.Object
    arm_obj = bpy.context.object
    bpy_bones = {}
    for bpy_bone in arm_obj.data.bones:
        bpy_bones[bpy_bone.name.lower()] = bpy_bone
    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == chunks.PARTITIONS1:
            pass
        else:
            bone_index = chunk_id
            _import_bone_data(chunk_data, arm_obj.name, bpy_bones, bone_index)


def import_file(filepath):
    with open(filepath, 'rb') as file:
        data = file.read()
    _import_main(data)
