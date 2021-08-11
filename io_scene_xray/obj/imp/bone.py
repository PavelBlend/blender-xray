# blender modules
import bpy
import mathutils

# addon modules
from ... import log, xray_io, xray_motions, utils
from ...version_utils import IS_28
from .. import fmt
from . import main


def _get_real_bone_shape():
    result = bpy.data.objects.get('real_bone_shape')
    if result is None:
        result = bpy.data.objects.new('real_bone_shape', None)
        display_type = 'SPHERE'
        if IS_28:
            result.empty_display_type = display_type
        else:
            result.empty_draw_type = display_type
    return result


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
            log.warn('bone VMap: will be renamed', vmap=vmap, name=name)
        elif ex != name:
            log.warn(
                'bone VMap: is already renamed',
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
                log.warn('bone parent isn\'t found', bone=name, parent=parent)
        bpy_bone.tail.y = 0.02
        bpy_bone.matrix = mat
        name = bpy_bone.name
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
    pose_bone = bpy_arm_obj.pose.bones[name]
    if context.operator.shaped_bones:
        pose_bone.custom_shape = _get_real_bone_shape()
    bpy_bone = bpy_armature.bones[name]
    xray = bpy_bone.xray
    xray.version = context.version
    xray.length = length
    return bpy_bone


def _safe_assign_enum_property(obj, pname, val, desc):
    defval = getattr(obj, pname)
    try:
        setattr(obj, pname, val)
    except TypeError:
        log.warn(
            'unsupported %s %s, using default' % (desc, pname),
            value=val,
            default=defval,
        )


@log.with_context(name='bone')
def import_bone(context, creader, bpy_arm_obj, renamemap):
    ver = creader.nextf(fmt.Chunks.Bone.VERSION, 'H')[0]
    if ver != 0x2:
        raise utils.AppError(
            'unsupported BONE format version', log.props(version=ver)
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
                    'Not supported yet! bone name != bone def2',
                    name=name,
                    def2=def2
                )
        elif cid == fmt.Chunks.Bone.MATERIAL:
            xray.gamemtl = xray_io.PackedReader(data).gets()
        elif cid == fmt.Chunks.Bone.SHAPE:
            reader = xray_io.PackedReader(data)
            _safe_assign_enum_property(
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
            _safe_assign_enum_property(ik, 'type', value, 'bone ikjoint')

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
