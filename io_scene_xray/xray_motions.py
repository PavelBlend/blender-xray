import bpy
from mathutils import Matrix, Euler, Quaternion

from .utils import is_exportable_bone, find_bone_exportable_parent, AppError
from .xray_envelope import Behavior, Shape, KF, EPSILON, refine_keys, export_keyframes
from .xray_io import PackedWriter, FastBytes as fb
from .log import warn, with_context, props as log_props
from .version_utils import multiply, get_multiply


MATRIX_BONE = Matrix((
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, -1.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0)
)).freeze()
MATRIX_BONE_INVERTED = MATRIX_BONE.inverted().freeze()

MOTIONS_FILTER_ALL = lambda name: True


@with_context('import-motion')
def import_motion(reader, context, bonesmap, reported, motions_filter=MOTIONS_FILTER_ALL):
    bpy_armature = context.bpy_arm_obj
    name = reader.gets()

    if not motions_filter(name):
        skip = _skip_motion_rest(reader.getv(), 0)
        reader.skip(skip)
        return
    act = bpy.data.actions.new(name=name)
    act.use_fake_user = True
    xray = act.xray
    reader.getf('II')  # range
    fps, ver = reader.getf('fH')
    xray.fps = fps
    if ver < 6:
        raise AppError('unsupported motions version', log_props(version=ver))

    if context.add_actions_to_motion_list:
        motion = bpy_armature.xray.motions_collection.add()
        motion.name = act.name
    else:
        motion = None

    if context.use_motion_prefix_name:
        bpy_armature.xray.use_custom_motion_names = True
        # cut extension
        filename = context.filename[0 : -len(context.filename.split('.')[-1]) - 1]
        name = '{0}_{1}'.format(filename, name)
        act.name = name
        if motion:
            motion.export_name = name
            motion.name = name

    if name != act.name and not context.use_motion_prefix_name and motion:
        bpy_armature.xray.use_custom_motion_names = True
        motion.export_name = name

    xray.flags, xray.bonepart = reader.getf('<BH')
    xray.speed, xray.accrue, xray.falloff, xray.power = reader.getf('<ffff')
    multiply = get_multiply()
    for _bone_idx in range(reader.getf('H')[0]):
        tmpfc = [act.fcurves.new('temp', index=i) for i in range(6)]
        try:
            times = {}
            bname = reader.gets()
            flags = reader.getf('B')[0]
            if flags != 0:
                warn('bone has non-zero flags', bone=bname, flags=flags)
            for fcurve in tmpfc:
                behaviors = reader.getf('BB')
                if (behaviors[0] != 1) or (behaviors[1] != 1):
                    warn('bone has different behaviors', bode=bname, behaviors=behaviors)
                for _keyframe_idx in range(reader.getf('H')[0]):
                    val = reader.getf('f')[0]
                    time = reader.getf('f')[0] * fps
                    times[time] = True
                    key_frame = fcurve.keyframe_points.insert(time, val)
                    shape = Shape(reader.getf('B')[0])
                    if shape != Shape.STEPPED:
                        reader.getf('HHH')
                        reader.getf('HHHH')
                    else:
                        key_frame.interpolation = 'CONSTANT'
            bpy_bone = bpy_armature.data.bones.get(bname, None)
            if bpy_bone is None:
                bpy_bone = bonesmap.get(bname.lower(), None)
                if bpy_bone is None:
                    if bname not in reported:
                        warn('bone is not found', bone=bname)
                        reported.add(bname)
                    continue
                if bname not in reported:
                    warn(
                        'bone\'s reference will be replaced',
                        bone=bname,
                        replacement=bpy_bone.name
                    )
                    reported.add(bname)
                bname = bpy_bone.name
            data_path = 'pose.bones["' + bname + '"]'
            fcs = [
                act.fcurves.new(data_path + '.location', index=0, action_group=bname),
                act.fcurves.new(data_path + '.location', index=1, action_group=bname),
                act.fcurves.new(data_path + '.location', index=2, action_group=bname),
                act.fcurves.new(data_path + '.rotation_euler', index=0, action_group=bname),
                act.fcurves.new(data_path + '.rotation_euler', index=1, action_group=bname),
                act.fcurves.new(data_path + '.rotation_euler', index=2, action_group=bname)
            ]
            xmat = bpy_bone.matrix_local.inverted()
            real_parent = find_bone_exportable_parent(bpy_bone)
            if real_parent:
                xmat = multiply(xmat, real_parent.matrix_local)
            else:
                xmat = multiply(xmat, MATRIX_BONE)
            for time in times:
                mat = multiply(
                    xmat,
                    Matrix.Translation((
                        +tmpfc[0].evaluate(time),
                        +tmpfc[1].evaluate(time),
                        -tmpfc[2].evaluate(time),
                    )),
                    Euler((
                        -tmpfc[4].evaluate(time),
                        -tmpfc[3].evaluate(time),
                        +tmpfc[5].evaluate(time),
                    ), 'ZXY').to_matrix().to_4x4()
                )
                trn = mat.to_translation()
                rot = mat.to_euler('ZXY')
                for i in range(3):
                    fcs[i + 0].keyframe_points.insert(time, trn[i])
                for i in range(3):
                    fcs[i + 3].keyframe_points.insert(time, rot[i])
        finally:
            for fcurve in tmpfc:
                act.fcurves.remove(fcurve)
    if ver >= 7:
        for _bone_idx in range(reader.getf('I')[0]):
            name = reader.gets_a()
            reader.skip((4 + 4) * reader.getf('I')[0])
            warn('markers are not supported yet', name=name)
    return act


def import_motions(reader, context, motions_filter=MOTIONS_FILTER_ALL):
    bpy_armature = context.bpy_arm_obj
    motions_count = reader.getf('I')[0]
    if motions_count:
        bonesmap = {b.name.lower(): b for b in bpy_armature.data.bones}
        reported = set()
        for _ in range(motions_count):
            import_motion(reader, context, bonesmap, reported, motions_filter)


@with_context('examine-motion')
def _examine_motion(data, offs):
    name, ptr = fb.str_at(data, offs)
    ptr = _skip_motion_rest(data, ptr)
    return name, ptr


def _skip_motion_rest(data, offs):
    ptr = offs + 4 + 4 + 4 + 2
    ver = fb.short_at(data, ptr - 2)
    if ver < 6:
        raise AppError('unsupported motions version', log_props(version=ver))

    ptr += (1 + 2 + 4 * 4) + 2
    for _bone_idx in range(fb.short_at(data, ptr - 2)):
        ptr = fb.skip_str_at(data, ptr) + 1
        for _fcurve_idx in range(6):
            ptr += 1 + 1 + 2
            for _kf_idx in range(fb.short_at(data, ptr - 2)):
                ptr += (4 + 4) + 1
                shape = data[ptr - 1]
                if shape != 4:
                    ptr += (2 * 3 + 2 * 4)
    if ver >= 7:
        ptr += 4
        for _bone_idx in range(fb.int_at(data, ptr - 4)):
            ptr = fb.skip_str_at_a(data, ptr) + 4
            ptr += (4 + 4) * fb.int_at(data, ptr - 4)

    return ptr


def examine_motions(data):
    offs = 4
    for _ in range(fb.int_at(data, offs - 4)):
        name, offs = _examine_motion(data, offs)
        yield name


@with_context('export-motion')
def export_motion(pkw, action, armature):
    dependency_object = None
    if armature.xray.dependency_object:
        dependency_object = bpy.data.objects.get(armature.xray.dependency_object)
        if dependency_object:
            old_action = dependency_object.animation_data.action
            dependency_object.animation_data.action = action

    prepared_bones = _prepare_bones(armature)
    bones_animations = _bake_motion_data(action, armature, prepared_bones)
    _export_motion_data(pkw, action, bones_animations, armature)

    if dependency_object:
        dependency_object.animation_data.action = old_action


def _bake_motion_data(action, armature, prepared_bones):
    exportable_bones = [(bone, parent, []) for bone, parent in prepared_bones]

    has_old_action = False
    if armature.animation_data:
        old_act = armature.animation_data.action
        has_old_action = True
    else:
        armature.animation_data_create()
    old_frame = bpy.context.scene.frame_current
    try:
        armature.animation_data.action = action
        for frm in range(int(action.frame_range[0]), int(action.frame_range[1]) + 1):
            bpy.context.scene.frame_set(frm)
            for pbone, parent, data in exportable_bones:
                parent_matrix = parent.matrix.inverted() if parent else MATRIX_BONE_INVERTED
                data.append(multiply(parent_matrix, pbone.matrix))
    finally:
        if has_old_action:
            armature.animation_data.action = old_act
        bpy.context.scene.frame_set(old_frame)

    return [
        (pbone.name, animation)
        for pbone, _, animation in exportable_bones
    ]


def _prepare_bones(armature):
    def prepare_bone(bone):
        real_parent = find_bone_exportable_parent(bone)
        return (
            armature.pose.bones[bone.name],
            armature.pose.bones[real_parent.name] if real_parent else None
        )

    return [
        prepare_bone(bone)
        for bone in armature.data.bones if is_exportable_bone(bone)
    ]


def _export_motion_data(pkw, action, bones_animations, armature):
    xray = action.xray

    if armature.xray.use_custom_motion_names:
        motion = armature.xray.motions_collection.get(action.name)
        if motion.export_name:
            motion_name = motion.export_name
        else:
            motion_name = action.name
    else:
        motion_name = action.name

    pkw.puts(motion_name)
    motion_name
    frange = action.frame_range
    pkw.putf('II', int(frange[0]), int(frange[1]))
    pkw.putf('f', xray.fps)
    pkw.putf('H', 6)  # version
    pkw.putf('<BH', xray.flags, xray.bonepart)
    pkw.putf('<ffff', xray.speed, xray.accrue, xray.falloff, xray.power)
    pkw.putf('H', len(bones_animations))
    for name, animation in bones_animations:
        pkw.puts(name)
        pkw.putf('B', 0)  # flags
        curves = ([], [], [], [], [], [])

        for mat in animation:
            trn = mat.to_translation()
            rot = mat.to_euler('ZXY')
            curves[0].append(+trn[0])
            curves[1].append(+trn[1])
            curves[2].append(-trn[2])
            curves[3].append(-rot[1])
            curves[4].append(-rot[0])
            curves[5].append(+rot[2])

        def curve2keys(curve):
            for frm, val in enumerate(curve):
                yield KF(frm / xray.fps, val, Shape.STEPPED)

        for i, curve in enumerate(curves):
            epsilon = EPSILON
            if xray.autobake_custom_refine:
                epsilon = xray.autobake_refine_location if i < 3 else xray.autobake_refine_rotation

            pkw.putf('BB', Behavior.CONSTANT.value, Behavior.CONSTANT.value)
            cpkw = PackedWriter()
            ccnt = export_keyframes(cpkw, refine_keys(curve2keys(curve), epsilon))
            pkw.putf('H', ccnt)
            pkw.putp(cpkw)


def export_motions(writer, actions, bpy_armature):
    writer.putf('I', len(actions))
    for action in actions:
        export_motion(writer, action, bpy_armature)
