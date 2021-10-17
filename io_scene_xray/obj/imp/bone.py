# blender modules
import bpy
import mathutils

# addon modules
from . import main
from .. import fmt
from ... import text
from ... import log
from ... import xray_io
from ... import xray_motions
from ... import utils
from ... import version_utils


def _create_bone(
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
            log.warn(text.warn.object_bone_renamed, vmap=vmap, name=name)
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
        rot = mathutils.Euler(
            (-rotate[0], -rotate[1], -rotate[2]), 'YXZ'
        ).to_matrix().to_4x4()
        mat = context.multiply(
            mathutils.Matrix.Translation(offset),
            rot,
            xray_motions.MATRIX_BONE
        )
        if parent:
            bpy_bone.parent = bpy_armature.edit_bones.get(parent, None)
            if bpy_bone.parent:
                mat = context.multiply(
                    bpy_bone.parent.matrix,
                    xray_motions.MATRIX_BONE_INVERTED,
                    mat
                )
            else:
                log.warn(
                    text.warn.no_bone_parent,
                    bone=name,
                    parent=parent
                )
        bpy_bone.tail.y = 0.02
        bpy_bone.matrix = mat
        name = bpy_bone.name
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
    pose_bone = bpy_arm_obj.pose.bones[name]
    bpy_bone = bpy_armature.bones[name]
    xray = bpy_bone.xray
    xray.version = context.version
    xray.length = length
    return bpy_bone


def safe_assign_enum_property(obj, pname, val, desc):
    defval = getattr(obj, pname)
    try:
        setattr(obj, pname, val)
    except TypeError:
        log.warn(
            text.warn.object_unsupport_prop,
            value=val,
            default=defval,
        )


@log.with_context(name='bone')
def import_bone(context, creader, bpy_arm_obj, renamemap):
    ver = creader.nextf(fmt.Chunks.Bone.VERSION, 'H')[0]
    if ver != 0x2:
        raise utils.AppError(
            text.error.object_unsupport_bone_ver,
            log.props(version=ver)
        )

    reader = xray_io.PackedReader(creader.next(fmt.Chunks.Bone.DEF))
    name = reader.gets()
    log.update(name=name)
    parent = reader.gets()
    vmap = reader.gets()

    reader = xray_io.PackedReader(creader.next(fmt.Chunks.Bone.BIND_POSE))
    offset = main.read_v3f(reader)
    rotate = main.read_v3f(reader)
    length = reader.getf('f')[0]

    bpy_bone = _create_bone(
        context, bpy_arm_obj,
        name, parent,
        vmap,
        offset, rotate, length,
        renamemap,
    )
    xray = bpy_bone.xray
    for (cid, data) in creader:
        if cid == fmt.Chunks.Bone.DEF:
            def2 = xray_io.PackedReader(data).gets()
            if name != def2:
                log.warn(
                    text.warn.object_bad_bone_name,
                    name=name,
                    def2=def2
                )
        elif cid == fmt.Chunks.Bone.MATERIAL:
            xray.gamemtl = xray_io.PackedReader(data).gets()
        elif cid == fmt.Chunks.Bone.SHAPE:
            reader = xray_io.PackedReader(data)
            safe_assign_enum_property(
                xray.shape,
                'type',
                str(reader.getf('H')[0]),
                'bone shape'
            )
            xray.shape.flags = reader.getf('H')[0]
            xray.shape.box_rot = reader.getf('fffffffff')
            xray.shape.box_trn = reader.getf('fff')
            xray.shape.box_hsz = reader.getf('fff')
            xray.shape.sph_pos = reader.getf('fff')
            xray.shape.sph_rad = reader.getf('f')[0]
            xray.shape.cyl_pos = reader.getf('fff')
            xray.shape.cyl_dir = reader.getf('fff')
            xray.shape.cyl_hgh = reader.getf('f')[0]
            xray.shape.cyl_rad = reader.getf('f')[0]
            xray.shape.set_curver()
        elif cid == fmt.Chunks.Bone.IK_JOINT:
            reader = xray_io.PackedReader(data)
            pose_bone = bpy_arm_obj.pose.bones[name]
            value = str(reader.int())
            ik = xray.ikjoint
            safe_assign_enum_property(ik, 'type', value, 'bone ikjoint')

            ik.lim_x_min, ik.lim_x_max = reader.getf('ff')
            ik.lim_x_spr, ik.lim_x_dmp = reader.getf('ff')

            ik.lim_y_min, ik.lim_y_max = reader.getf('ff')
            ik.lim_y_spr, ik.lim_y_dmp = reader.getf('ff')

            ik.lim_z_min, ik.lim_z_max = reader.getf('ff')
            ik.lim_z_spr, ik.lim_z_dmp = reader.getf('ff')

            ik.spring = reader.getf('f')[0]
            ik.damping = reader.getf('f')[0]

        elif cid == fmt.Chunks.Bone.MASS_PARAMS:
            reader = xray_io.PackedReader(data)
            xray.mass.value = reader.getf('f')[0]
            xray.mass.center = main.read_v3f(reader)
        elif cid == fmt.Chunks.Bone.IK_FLAGS:
            xray.ikflags = xray_io.PackedReader(data).int()
        elif cid == fmt.Chunks.Bone.BREAK_PARAMS:
            reader = xray_io.PackedReader(data)
            xray.breakf.force = reader.getf('f')[0]
            xray.breakf.torque = reader.getf('f')[0]
        elif cid == fmt.Chunks.Bone.FRICTION:
            xray.friction = xray_io.PackedReader(data).getf('f')[0]
        else:
            log.debug('unknown chunk', cid=cid)
