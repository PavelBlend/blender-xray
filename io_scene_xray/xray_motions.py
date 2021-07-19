import bpy
from mathutils import Matrix, Euler, Quaternion

from .utils import is_exportable_bone, find_bone_exportable_parent, AppError
from .xray_envelope import (
    Behavior, Shape, KF, EPSILON, refine_keys, export_keyframes
)
from .xray_io import PackedWriter, FastBytes as fb
from .log import warn, with_context, props as log_props
from .version_utils import multiply, get_multiply
from . import xray_interpolation


MATRIX_BONE = Matrix((
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, -1.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0)
)).freeze()
MATRIX_BONE_INVERTED = MATRIX_BONE.inverted().freeze()

MOTIONS_FILTER_ALL = lambda name: True
CURVE_COUNT = 6    # translation xyz, rotation xyz


def interpolate_keys(fps, start, end, name, values, times, shapes, tcb):
    interpolated_values = []
    interpolated_times = []
    keys_count = len(values)
    for index, key_info in enumerate(zip(values, times, shapes, tcb)):
        value_1, time_1, shape_1, (tension_1, continuity_1, bias_1) = key_info
        if not shape_1 in (Shape.TCB, Shape.LINEAR):
            raise AppError('Unsupported shape: {}'.format(shape_1.name))
        index_2 = index + 1
        if keys_count == 1:
            # constant values
            for frame_index in range(start, end + 1):
                interpolated_values.append(value_1)
                interpolated_times.append(frame_index)
            continue
        if index_2 >= keys_count:
            interpolated_values.append(value_1)
            interpolated_times.append(int(round(time_1, 0)))
            continue
        value_2 = values[index_2]
        time_2 = times[index_2]
        shape_2 = shapes[index_2]
        tension_2, continuity_2, bias_2 = tcb[index_2]
        if index > 0:
            prev_time = times[index - 1]
            prev_value = values[index - 1]
        else:
            prev_time = None
            prev_value = None
        index_next = index_2 + 1
        if index_next < keys_count:
            next_time = times[index_next]
            next_value = values[index_next]
        else:
            next_time = None
            next_value = None
        start_frame = int(round(time_1, 0))
        end_frame = int(round(time_2, 0))
        for frame_index in range(start_frame, end_frame):
            interpolated_value = xray_interpolation.evaluate(
                shape_1.value,
                time_1, value_1, tension_1, continuity_1, bias_1,
                time_2, value_2, tension_2, continuity_2, bias_2,
                prev_time, prev_value, next_time, next_value, frame_index
            )
            interpolated_values.append(interpolated_value)
            interpolated_times.append(frame_index)
    return interpolated_values, interpolated_times


def convert_u16_to_float(u16_value, min_value, max_value):
    return (u16_value * (max_value - min_value)) / 65535 + min_value


@with_context('import-motion')
def import_motion(
        reader, context, bonesmap, reported,
        motions_filter=MOTIONS_FILTER_ALL, skl_file_name=None
    ):
    bpy_armature = context.bpy_arm_obj
    name = reader.gets()
    if skl_file_name:
        name = skl_file_name
    bone_maps = {}
    converted_warrnings = []

    if not motions_filter(name):
        skip = _skip_motion_rest(reader.getv(), 0)
        reader.skip(skip)
        return
    act = bpy.data.actions.new(name=name)
    act.use_fake_user = True
    xray = act.xray
    start_frame, end_frame = reader.getf('II')  # range
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
        action_name = '{0}_{1}'.format(filename, name)
        act.name = action_name
        if motion:
            motion.export_name = name
            motion.name = act.name

    if name != act.name and not context.use_motion_prefix_name and motion:
        bpy_armature.xray.use_custom_motion_names = True
        motion.export_name = name

    xray.flags, xray.bonepart = reader.getf('<BH')
    xray.speed, xray.accrue, xray.falloff, xray.power = reader.getf('<ffff')
    multiply = get_multiply()
    converted_shapes = []
    converted_shapes_names = set()
    for _bone_idx in range(reader.getf('H')[0]):
        bname = reader.gets()
        flags = reader.getf('B')[0]
        if flags != 0:
            warn('bone has non-zero flags', bone=bname, flags=flags)
        curves = [None, ] * CURVE_COUNT
        used_times = set()
        has_interpolate = False
        for curve_index in range(CURVE_COUNT):
            values = []
            times = []
            shapes = []
            tcb = []
            use_interpolate = False
            behaviors = reader.getf('BB')
            if (behaviors[0] != 1) or (behaviors[1] != 1):
                warn('bone has different behaviors', bone=bname, behaviors=behaviors)
            for _keyframe_idx in range(reader.getf('H')[0]):
                val = reader.getf('f')[0]
                time = reader.getf('f')[0] * fps
                shape = Shape(reader.getf('B')[0])
                values.append(val)
                times.append(time)
                shapes.append(shape)
                used_times.add(time)
                if shape != Shape.STEPPED:
                    tension, continuity, bias = reader.getf('HHH')
                    reader.getf('HHHH')
                    tcb.append((
                        convert_u16_to_float(tension, -32.0, 32.0),
                        convert_u16_to_float(continuity, -32.0, 32.0),
                        convert_u16_to_float(bias, -32.0, 32.0)
                    ))
                    use_interpolate = True
                    has_interpolate = True
                    converted_shapes.append((shape, name, bname))
                else:
                    tcb.append((None, None, None))
            if use_interpolate:
                curve_end_time = int(round(times[-1], 0))
                if curve_end_time < end_frame and curve_end_time:
                    times.append(end_frame)
                    values.append(values[-1])
                    shapes.append(shapes[-1])
                    tcb.append(tcb[-1])
                values, times = interpolate_keys(fps, start_frame, end_frame, name, values, times, shapes, tcb)
            curves[curve_index] = values, times
        used_times = set()
        if not has_interpolate:
            tmpfc = [act.fcurves.new('temp', index=i) for i in range(6)]
            for curve_index in range(CURVE_COUNT):
                fcurve = tmpfc[curve_index]
                for value, time in zip(*curves[curve_index]):
                    key_frame = fcurve.keyframe_points.insert(time, value)
                    key_frame.interpolation = 'CONSTANT'
                    used_times.add(time)
        bone_key = bname
        bpy_bone = bpy_armature.data.bones.get(bname, None)
        if bpy_bone is None:
            bpy_bone = bonesmap.get(bname.lower(), None)
            if bpy_bone is None:
                if bname.isdigit():
                    bone_id = int(bname)
                    if bone_id < len(bpy_armature.data.bones):
                        bpy_bone = bpy_armature.data.bones[bone_id]
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
        bone_maps[bone_key] = bname
        for shape, motion_name, bone_name in converted_shapes:
            converted_warrnings.append((
                'motion shape converted to STEPPED',
                motion_name,
                bone_maps[bone_name]
            ))
            converted_shapes_names.add(shape.name)
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
        if not has_interpolate:
            try:
                for time in used_times:
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
                        key_frame = fcs[i + 0].keyframe_points.insert(time, trn[i])
                        key_frame.interpolation = 'LINEAR'
                    for i in range(3):
                        key_frame = fcs[i + 3].keyframe_points.insert(time, rot[i])
                        key_frame.interpolation = 'LINEAR'
            finally:
                for fcurve in tmpfc:
                    act.fcurves.remove(fcurve)
        else:
            for index in range(end_frame - start_frame + 1):
                mat = multiply(
                    xmat,
                    Matrix.Translation((
                        +curves[0][0][index],
                        +curves[1][0][index],
                        -curves[2][0][index],
                    )),
                    Euler((
                        -curves[4][0][index],
                        -curves[3][0][index],
                        +curves[5][0][index],
                    ), 'ZXY').to_matrix().to_4x4()
                )
                trn = mat.to_translation()
                rot = mat.to_euler('ZXY')
                for i in range(3):
                    key_frame = fcs[i + 0].keyframe_points.insert(curves[i][1][index], trn[i])
                    key_frame.interpolation = 'LINEAR'
                for i in range(3):
                    key_frame = fcs[i + 3].keyframe_points.insert(curves[i + 3][1][index], rot[i])
                    key_frame.interpolation = 'LINEAR'
    for warn_message, motion_name, bone_name in set(converted_warrnings):
        keys_count = converted_warrnings.count((
            warn_message, motion_name, bone_name
        ))
        warn(
            warn_message,
            shapes=tuple(converted_shapes_names),
            motion=motion_name, bone=bone_name,
            keys_count=keys_count
        )
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
