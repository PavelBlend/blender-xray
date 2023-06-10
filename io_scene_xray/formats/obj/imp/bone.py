# blender modules
import bpy
import mathutils

# addon modules
from .. import fmt
from ... import motions
from .... import text
from .... import log
from .... import rw
from .... import utils


BONE_LENGTH = 0.02


def create_bone(
        context,
        bpy_arm_obj,
        name,
        parent,
        vmap,
        offset,
        rotate,
        length,
        renamemap
    ):

    bpy_armature = bpy_arm_obj.data

    if name != vmap:
        ex = renamemap.get(vmap, None)
        if ex is None:
            log.warn(
                text.warn.object_bone_renamed,
                vmap=vmap,
                name=name
            )
        elif ex != name:
            log.warn(
                text.warn.object_bone_already_renamed,
                vmap=vmap,
                name1=ex,
                name2=name
            )
        renamemap[vmap] = name

    bpy.ops.object.mode_set(mode='EDIT')

    try:
        bpy_bone = bpy_armature.edit_bones.new(name=name)
        rot = mathutils.Euler((-rotate[0], -rotate[1], -rotate[2]), 'YXZ')
        rot_mat = rot.to_matrix().to_4x4()
        mat = context.multiply(
            mathutils.Matrix.Translation(offset),
            rot_mat,
            motions.const.MATRIX_BONE
        )
        if parent:
            bpy_bone.parent = bpy_armature.edit_bones.get(parent, None)
            if bpy_bone.parent:
                mat = context.multiply(
                    bpy_bone.parent.matrix,
                    motions.const.MATRIX_BONE_INVERTED,
                    mat
                )
            else:
                log.warn(
                    text.warn.no_bone_parent,
                    parent=parent,
                    child=name
                )
        bpy_bone.tail.y = BONE_LENGTH
        bpy_bone.matrix = mat
        bone_name = bpy_bone.name

    finally:
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy_bone = bpy_armature.bones[bone_name]
    xray = bpy_bone.xray
    xray.version = context.version
    xray.length = length

    return bpy_bone


@log.with_context(name='bone')
def import_bone(
        context,
        chunks,
        bpy_arm_obj,
        renamemap,
        imported_bones,
        bones_chunks,
        bone_id_by_name
    ):

    data = chunks.get(fmt.Chunks.Bone.VERSION)
    reader = rw.read.PackedReader(data)
    ver = reader.getf('<H')[0]
    if ver != 0x2:
        raise log.AppError(
            text.error.object_unsupport_bone_ver,
            log.props(version=ver)
        )

    data = chunks.get(fmt.Chunks.Bone.DEF)
    reader = rw.read.PackedReader(data)
    name = reader.gets()
    log.update(bone=name)
    parent = reader.gets()
    vmap = reader.gets()

    if name in imported_bones:
        return

    data = chunks.get(fmt.Chunks.Bone.BIND_POSE)
    reader = rw.read.PackedReader(data)
    offset = reader.getv3fp()
    rotate = reader.getv3fp()
    length = reader.getf('<f')[0]

    if not bpy_arm_obj.data.bones.get(parent) and parent:
        bone_id = bone_id_by_name.get(parent, None)
        if bone_id:
            parent_chunks = bones_chunks[bone_id]
            import_bone(
                context,
                parent_chunks,
                bpy_arm_obj,
                renamemap,
                imported_bones,
                bones_chunks,
                bone_id_by_name
            )

    bpy_bone = create_bone(
        context, bpy_arm_obj,
        name, parent,
        vmap,
        offset, rotate, length,
        renamemap,
    )
    imported_bones.add(name)
    xray = bpy_bone.xray

    for cid, data in chunks.items():
        if cid == fmt.Chunks.Bone.DEF:
            def2 = rw.read.PackedReader(data).gets()
            if name != def2:
                log.warn(
                    text.warn.object_bad_bone_name,
                    name=name,
                    def2=def2
                )

        elif cid == fmt.Chunks.Bone.MATERIAL:
            xray.gamemtl = rw.read.PackedReader(data).gets()

        elif cid == fmt.Chunks.Bone.SHAPE:
            reader = rw.read.PackedReader(data)
            utils.bone.safe_assign_enum_property(
                bpy_bone.name,
                xray.shape,
                'type',
                reader.getf('<H')[0],
                text.get_text(text.warn.ogf_bad_shape),
                4
            )
            xray.shape.flags = reader.getf('<H')[0]
            xray.shape.box_rot = reader.getf('<9f')
            xray.shape.box_trn = reader.getf('<3f')
            xray.shape.box_hsz = reader.getf('<3f')
            xray.shape.sph_pos = reader.getf('<3f')
            xray.shape.sph_rad = reader.getf('<f')[0]
            xray.shape.cyl_pos = reader.getf('<3f')
            xray.shape.cyl_dir = reader.getf('<3f')
            xray.shape.cyl_hgh = reader.getf('<f')[0]
            xray.shape.cyl_rad = reader.getf('<f')[0]
            xray.shape.set_curver()

        elif cid == fmt.Chunks.Bone.IK_JOINT:
            reader = rw.read.PackedReader(data)
            value = reader.uint32()
            ik = xray.ikjoint
            utils.bone.safe_assign_enum_property(
                bpy_bone.name,
                ik,
                'type',
                value,
                text.get_text(text.warn.ogf_bad_joint),
                6
            )

            ik.lim_x_min, ik.lim_x_max = reader.getf('<2f')
            ik.lim_x_spr, ik.lim_x_dmp = reader.getf('<2f')

            ik.lim_y_min, ik.lim_y_max = reader.getf('<2f')
            ik.lim_y_spr, ik.lim_y_dmp = reader.getf('<2f')

            ik.lim_z_min, ik.lim_z_max = reader.getf('<2f')
            ik.lim_z_spr, ik.lim_z_dmp = reader.getf('<2f')

            ik.spring = reader.getf('<f')[0]
            ik.damping = reader.getf('<f')[0]

        elif cid == fmt.Chunks.Bone.MASS_PARAMS:
            reader = rw.read.PackedReader(data)
            xray.mass.value = reader.getf('<f')[0]
            xray.mass.center = reader.getv3fp()

        elif cid == fmt.Chunks.Bone.IK_FLAGS:
            xray.ikflags = rw.read.PackedReader(data).uint32()

        elif cid == fmt.Chunks.Bone.BREAK_PARAMS:
            reader = rw.read.PackedReader(data)
            xray.breakf.force = reader.getf('<f')[0]
            xray.breakf.torque = reader.getf('<f')[0]

        elif cid == fmt.Chunks.Bone.FRICTION:
            xray.friction = rw.read.PackedReader(data).getf('<f')[0]

        else:
            if not cid in (
                    fmt.Chunks.Bone.VERSION,
                    fmt.Chunks.Bone.DEF,
                    fmt.Chunks.Bone.BIND_POSE
                ):
                log.debug('unknown chunk', chunk_id=cid)
