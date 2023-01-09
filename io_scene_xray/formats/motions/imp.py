# blender modules
import bpy
import mathutils

# addon modules
from . import const
from . import interp
from . import utilites
from ... import log
from ... import text
from ... import utils
from ... import rw


def skip_motion_rest(data, offs):
    ptr = offs + 4 + 4 + 4 + 2
    ver = rw.read.FastBytes.short_at(data, ptr - 2)
    if ver < 6:
        raise log.AppError(text.error.motion_ver, log.props(version=ver))

    ptr += (1 + 2 + 4 * 4) + 2
    for _bone_idx in range(rw.read.FastBytes.short_at(data, ptr - 2)):
        ptr = rw.read.FastBytes.skip_str_at(data, ptr) + 1
        for _fcurve_idx in range(6):
            ptr += 1 + 1 + 2
            for _kf_idx in range(rw.read.FastBytes.short_at(data, ptr - 2)):
                ptr += (4 + 4) + 1
                shape = data[ptr - 1]
                if shape != 4:
                    ptr += (2 * 3 + 2 * 4)
    if ver >= 7:
        ptr += 4
        for _bone_idx in range(rw.read.FastBytes.int_at(data, ptr - 4)):
            ptr = rw.read.FastBytes.skip_str_at_a(data, ptr) + 4
            ptr += (4 + 4) * rw.read.FastBytes.int_at(data, ptr - 4)

    return ptr


@log.with_context('motion')
def import_motion(
        reader,
        context,
        bonesmap,
        reported,
        motions_filter=utilites.MOTIONS_FILTER_ALL,
        skl_file_name=None
    ):
    bpy_armature = context.bpy_arm_obj
    name = reader.gets()
    log.update(motion=name)
    if skl_file_name:
        name = skl_file_name
    bone_maps = {}
    converted_warrnings = []

    if not motions_filter(name):
        skip = skip_motion_rest(reader.getv(), 0)
        reader.skip(skip)
        return
    act = bpy.data.actions.new(name=name)
    act.use_fake_user = True
    xray = act.xray
    start_frame, end_frame = reader.getf('<2I')
    fps, ver = reader.getf('<fH')
    xray.fps = fps
    if ver < 6:
        raise log.AppError(text.error.motion_ver, log.props(version=ver))

    if context.add_actions_to_motion_list:
        motion = bpy_armature.xray.motions_collection.add()
        motion.name = act.name
    else:
        motion = None

    if name != act.name and motion:
        bpy_armature.xray.use_custom_motion_names = True
        motion.export_name = name

    xray.flags, xray.bonepart = reader.getf('<BH')
    xray.speed, xray.accrue, xray.falloff, xray.power = reader.getf('<4f')
    multiply = utils.version.get_multiply()
    converted_shapes = []
    converted_shapes_names = set()
    for _bone_idx in range(reader.getf('H')[0]):
        bname = reader.gets()
        flags = reader.getf('B')[0]
        if flags != 0:
            log.warn(text.warn.motion_non_zero_flags, bone=bname, flags=flags)
        curves = [None, ] * const.CURVE_COUNT
        used_times = set()
        has_interpolate = False
        for curve_index in range(const.CURVE_COUNT):
            values = []
            times = []
            shapes = []
            tcb = []
            params = []
            use_interpolate = False
            behaviors = reader.getf('<2B')
            if (behaviors[0] != 1) or (behaviors[1] != 1):
                log.warn(
                    text.warn.motion_behaviors,
                    bone=bname,
                    behaviors=behaviors
                )
            frame_time = 1
            val_raw_prev = None
            val_prev = None
            time_prev = 1000000.0
            for _keyframe_idx in range(reader.getf('<H')[0]):
                val_raw = reader.getb32()
                val = reader.getf('<f')[0]
                time = reader.getf('<f')[0] * fps
                shape = interp.Shape(reader.getf('<B')[0])
                if shape == interp.Shape.STEPPED:
                    if val_raw != val_raw_prev:
                        if (time - time_prev) > frame_time:
                            values.append(val_prev)
                            times.append(time - frame_time)
                            shapes.append(shape)
                            used_times.add(time - frame_time)
                            tcb.append((0.0, 0.0, 0.0))
                            params.append((0.0, 0.0, 0.0, 0.0))
                values.append(val)
                times.append(time)
                shapes.append(shape)
                used_times.add(time)
                if shape != interp.Shape.STEPPED:
                    tension = reader.getq16f(-32.0, 32.0)
                    continuity = reader.getq16f(-32.0, 32.0)
                    bias = reader.getq16f(-32.0, 32.0)
                    param = []
                    for param_index in range(4):
                        param_value = reader.getq16f(-32.0, 32.0)
                        param.append(param_value)
                    tcb.append((tension, continuity, bias))
                    params.append(param)
                    use_interpolate = True
                    has_interpolate = True
                    converted_shapes.append((shape, name, bname))
                else:
                    tcb.append((0.0, 0.0, 0.0))
                    params.append((0.0, 0.0, 0.0, 0.0))
                val_raw_prev = val_raw
                val_prev = val
                time_prev = time
            if use_interpolate:
                curve_end_time = int(round(times[-1], 0))
                if curve_end_time < end_frame and curve_end_time:
                    times.append(end_frame)
                    values.append(values[-1])
                    shapes.append(shapes[-1])
                    tcb.append(tcb[-1])
                    params.append(params[-1])
                values, times = interpolate_keys(fps, start_frame, end_frame, values, times, shapes, tcb, params)
            curves[curve_index] = values, times
        used_times = set()
        if not has_interpolate:
            tmpfc = [
                act.fcurves.new('temp', index=curve_index)
                for curve_index in range(6)
            ]
            for curve_index in range(const.CURVE_COUNT):
                fcurve = tmpfc[curve_index]
                for value, time in zip(*curves[curve_index]):
                    key_frame = fcurve.keyframe_points.insert(time, value)
                    key_frame.interpolation = 'LINEAR'
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
                        log.warn(text.warn.motion_no_bone, bone=bname)
                        reported.add(bname)
                    for fcurve in tmpfc:
                        act.fcurves.remove(fcurve)
                    continue
            if bname not in reported:
                log.warn(
                    text.warn.motion_bone_replaced,
                    bone=bname,
                    replacement=bpy_bone.name
                )
                reported.add(bname)
            bname = bpy_bone.name
        pose_bone = bpy_armature.pose.bones[bpy_bone.name]
        if pose_bone.rotation_mode != 'ZXY':
            log.warn(
                text.warn.motion_rotation_mode,
                object=bpy_armature.name,
                bone=pose_bone.name,
                rotation_mode=pose_bone.rotation_mode
            )
        bone_maps[bone_key] = bname
        for shape, motion_name, bone_name in converted_shapes:
            converted_warrnings.append((
                text.warn.motion_to_stepped,
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
        real_parent = utils.bone.find_bone_exportable_parent(bpy_bone)
        if real_parent:
            xmat = multiply(xmat, real_parent.matrix_local)
        else:
            xmat = multiply(xmat, const.MATRIX_BONE)
        if not has_interpolate:
            try:
                for time in used_times:
                    mat = multiply(
                        xmat,
                        mathutils.Matrix.Translation((
                            +tmpfc[0].evaluate(time),
                            +tmpfc[1].evaluate(time),
                            -tmpfc[2].evaluate(time),
                        )),
                        mathutils.Euler((
                            -tmpfc[4].evaluate(time),
                            -tmpfc[3].evaluate(time),
                            +tmpfc[5].evaluate(time),
                        ), 'ZXY').to_matrix().to_4x4()
                    )
                    trn = mat.to_translation()
                    rot = mat.to_euler('ZXY')
                    for axis in range(3):
                        key_frame = fcs[axis].keyframe_points.insert(time, trn[axis])
                        key_frame.interpolation = 'LINEAR'
                    for axis in range(3):
                        key_frame = fcs[axis + 3].keyframe_points.insert(time, rot[axis])
                        key_frame.interpolation = 'LINEAR'
            finally:
                for fcurve in tmpfc:
                    act.fcurves.remove(fcurve)
        else:
            for index in range(end_frame - start_frame + 1):
                mat = multiply(
                    xmat,
                    mathutils.Matrix.Translation((
                        +curves[0][0][index],
                        +curves[1][0][index],
                        -curves[2][0][index],
                    )),
                    mathutils.Euler((
                        -curves[4][0][index],
                        -curves[3][0][index],
                        +curves[5][0][index],
                    ), 'ZXY').to_matrix().to_4x4()
                )
                trn = mat.to_translation()
                rot = mat.to_euler('ZXY')
                for axis in range(3):
                    key_frame = fcs[axis].keyframe_points.insert(
                        curves[axis][1][index],
                        trn[axis]
                    )
                    key_frame.interpolation = 'LINEAR'
                for axis in range(3):
                    key_frame = fcs[axis + 3].keyframe_points.insert(
                        curves[axis + 3][1][index],
                        rot[axis]
                    )
                    key_frame.interpolation = 'LINEAR'
    for warn_message, motion_name, bone_name in set(converted_warrnings):
        keys_count = converted_warrnings.count((
            warn_message, motion_name, bone_name
        ))
        log.warn(
            warn_message,
            shapes=tuple(converted_shapes_names),
            motion=motion_name, bone=bone_name,
            keys_count=keys_count
        )
    if ver >= 7:
        for _bone_idx in range(reader.getf('I')[0]):
            name = reader.gets_a()
            reader.skip((4 + 4) * reader.getf('I')[0])
            log.warn(text.warn.motion_markers, name=name)
    return act


def import_motions(reader, context, motions_filter=utilites.MOTIONS_FILTER_ALL):
    bpy_armature = context.bpy_arm_obj
    motions_count = reader.getf('I')[0]
    if motions_count:
        bonesmap = {
            bone.name.lower(): bone
            for bone in bpy_armature.data.bones
        }
        reported = set()
        for _ in range(motions_count):
            import_motion(reader, context, bonesmap, reported, motions_filter)


@log.with_context('examine-motion')
def _examine_motion(data, offs):
    name, ptr = rw.read.FastBytes.str_at(data, offs)
    ptr = skip_motion_rest(data, ptr)
    return name, ptr


def examine_motions(data):
    offs = 4
    for _ in range(rw.read.FastBytes.int_at(data, offs - 4)):
        name, offs = _examine_motion(data, offs)
        yield name


def interpolate_keys(fps, start, end, values, times, shapes, tcb, params):
    interpolated_values = []
    interpolated_times = []
    keys_count = len(values)
    unsupported_shapes = set()
    errors = {}
    for index_start, key_info in enumerate(zip(values, times, shapes, tcb, params)):
        value_start, time_start, shape_start, tcb_start, params_start = key_info
        if not shape_start in (
                interp.Shape.TCB,
                interp.Shape.HERMITE,
                interp.Shape.BEZIER_1D,
                interp.Shape.LINEAR,
                interp.Shape.STEPPED,
                interp.Shape.BEZIER_2D
            ):
            unsupported_shapes.add(shape_start.name)
            errors[shape_start.name] = errors.setdefault(shape_start.name, 0) + 1
            continue
        index_end = index_start + 1
        if keys_count == 1:
            # constant values
            for frame_index in range(start, end + 1):
                interpolated_values.append(value_start)
                interpolated_times.append(frame_index)
            continue
        if index_end >= keys_count:
            interpolated_values.append(value_start)
            interpolated_times.append(int(round(time_start, 0)))
            continue
        value_end = values[index_end]
        time_end = times[index_end]
        shape_end = shapes[index_end]
        tcb_end = tcb[index_end]
        params_end = params[index_end]
        if index_start > 0:
            prev_time = times[index_start - 1]
            prev_value = values[index_start - 1]
        else:
            prev_time = None
            prev_value = None
        index_next = index_end + 1
        if index_next < keys_count:
            next_time = times[index_next]
            next_value = values[index_next]
        else:
            next_time = None
            next_value = None
        start_frame = int(round(time_start, 0))
        end_frame = int(round(time_end, 0))

        # start key
        start_key = interp.Key()
        start_key.time = time_start
        start_key.value = value_start
        start_key.shape = shape_start
        start_key.tension = tcb_start[0]
        start_key.continuity = tcb_start[1]
        start_key.bias = tcb_start[2]
        start_key.param_1 = params_start[0]
        start_key.param_2 = params_start[1]
        start_key.param_3 = params_start[2]
        start_key.param_4 = params_start[3]
        # end key
        end_key = interp.Key()
        end_key.time = time_end
        end_key.value = value_end
        end_key.shape = shape_end
        end_key.tension = tcb_end[0]
        end_key.continuity = tcb_end[1]
        end_key.bias = tcb_end[2]
        end_key.param_1 = params_end[0]
        end_key.param_2 = params_end[1]
        end_key.param_3 = params_end[2]
        end_key.param_4 = params_end[3]
        # next key
        next_key = interp.Key()
        next_key.time = next_time
        next_key.value = next_value
        # preview key
        prev_key = interp.Key()
        prev_key.time = prev_time
        prev_key.value = prev_value
        for frame_index in range(start_frame, end_frame):
            interpolated_value = interp.evaluate(
                frame_index, start_key, end_key, prev_key, next_key
            )
            interpolated_values.append(interpolated_value)
            interpolated_times.append(frame_index)
    if unsupported_shapes:
        raise log.AppError(
            text.error.motion_shape,
            log.props(shapes=unsupported_shapes, count=errors)
        )
    return interpolated_values, interpolated_times
