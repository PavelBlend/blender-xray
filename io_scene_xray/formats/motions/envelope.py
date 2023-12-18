# addon modules
from . import imp
from . import write
from . import const
from . import interp
from . import utilites
from ... import log
from ... import text
from ... import rw
from ... import utils


@log.with_context('envelope')
def import_envelope(reader, ver, fcurve, fps, koef, name, warn_list, unique_shapes):
    bhv_fmt = 'I'
    if ver > 3:
        bhv_fmt = 'B'
    bhv0, bhv1 = map(interp.Behavior, reader.getf('<2' + bhv_fmt))

    if bhv0 != bhv1:
        log.warn(
            text.warn.envelope_behaviors_replaced,
            behavior=bhv1.name,
            replacement=bhv0.name
        )
        bhv1 = bhv0
    if bhv0 == interp.Behavior.CONSTANT:
        fcurve.extrapolation = 'CONSTANT'
    elif bhv0 == interp.Behavior.LINEAR:
        fcurve.extrapolation = 'LINEAR'
    else:
        bhv1 = interp.Behavior.CONSTANT
        log.warn(
            text.warn.envelope_bad_behavior,
            behavior=bhv0.name,
            replacement=bhv1.name
        )
        bhv0 = bhv1
        fcurve.extrapolation = 'CONSTANT'

    replace_unsupported_to = 'BEZIER'
    unsupported_occured = set()
    use_interpolate = False
    values = []
    times = []
    shapes = []
    tcb = []
    params = []
    count_fmt = 'I'
    if ver > 3:
        count_fmt = 'H'
    keyframes_count = reader.getf('<' + count_fmt)[0]
    if ver > 3:
        for _ in range(keyframes_count):
            value = reader.getf('<f')[0]
            time = reader.getf('<f')[0] * fps
            shape = interp.Shape(reader.getf('<B')[0])
            if shape != interp.Shape.STEPPED:
                tension = reader.getq16f(-32.0, 32.0)
                continuity = reader.getq16f(-32.0, 32.0)
                bias = reader.getq16f(-32.0, 32.0)
                param = []
                for param_index in range(4):
                    param_value = reader.getq16f(-32.0, 32.0)
                    param.append(param_value)
            else:
                tension = 0.0
                continuity = 0.0
                bias = 0.0
                param = (0.0, 0.0, 0.0, 0.0)
            values.append(value)
            times.append(time)
            shapes.append(shape)
            tcb.append((tension, continuity, bias))
            params.append(param)
            if shape not in (
                    interp.Shape.TCB,
                    interp.Shape.HERMITE,
                    interp.Shape.BEZIER_1D,
                    interp.Shape.LINEAR,
                    interp.Shape.STEPPED,
                    interp.Shape.BEZIER_2D
                ):
                unsupported_occured.add(shape.name)
            unique_shapes.add(shape.name)
            if shape in (
                    interp.Shape.TCB,
                    interp.Shape.HERMITE,
                    interp.Shape.BEZIER_1D,
                    interp.Shape.BEZIER_2D
                ):
                use_interpolate = True
    else:
        for _ in range(keyframes_count):
            value = reader.getf('<f')[0]
            time = reader.getf('<f')[0] * fps
            shape = interp.Shape(reader.uint32() & 0xff)
            tension, continuity, bias = reader.getf('<3f')
            param = reader.getf('<4f')    # params
            values.append(value)
            times.append(time)
            shapes.append(shape)
            tcb.append((tension, continuity, bias))
            params.append(param)
            if shape not in (
                    interp.Shape.TCB,
                    interp.Shape.HERMITE,
                    interp.Shape.BEZIER_1D,
                    interp.Shape.LINEAR,
                    interp.Shape.STEPPED,
                    interp.Shape.BEZIER_2D
                ):
                unsupported_occured.add(shape.name)
            unique_shapes.add(shape.name)
            if shape in (
                    interp.Shape.TCB,
                    interp.Shape.HERMITE,
                    interp.Shape.BEZIER_1D,
                    interp.Shape.BEZIER_2D
                ):
                use_interpolate = True

    frames_coords = []

    if use_interpolate:
        start_frame = int(round(times[0], 0))
        end_frame = int(round(times[-1], 0))
        values, times = imp.interpolate_keys(
            start_frame, end_frame, values, times, shapes, tcb, params
        )
        for time, value in zip(times, values):
            frames_coords.extend((time, value * koef))
        utils.action.insert_keyframes_for_single_curve(frames_coords, fcurve)

    else:
        key_count = len(times)
        interps = []
        for index, (time, value, shape_prev) in enumerate(zip(times, values, shapes)):
            frames_coords.extend((time, value * koef))
            if index + 1 < key_count:
                shape = shapes[index + 1]
            else:
                shape = shapes[-1]
            if shape == interp.Shape.LINEAR:
                interps.append('LINEAR')
            elif shape == interp.Shape.STEPPED:
                interps.append('CONSTANT')
            else:
                interps.append(replace_unsupported_to)
        utils.action.insert_keyframes_for_single_curve(
            frames_coords,
            fcurve,
            interps=interps
        )

    if unsupported_occured:
        warn_list.append((
            tuple(unsupported_occured),
            replace_unsupported_to,
            name
        ))

    return use_interpolate


@log.with_context('envelope')
def export_envelope(writer, ver, fcurve, fps, koef, epsilon=const.EPSILON):
    behavior = None
    if fcurve.extrapolation == 'CONSTANT':
        behavior = interp.Behavior.CONSTANT
    elif fcurve.extrapolation == 'LINEAR':
        behavior = interp.Behavior.LINEAR
    else:
        behavior = interp.Behavior.LINEAR
        log.warn(
            text.warn.envelope_extrapolation,
            extrapolation=fcurve.extrapolation,
            replacement=behavior.name
        )
    behav_fmt = 'I'
    if ver > 3:
        behav_fmt = 'B'
    writer.putf('<2' + behav_fmt, behavior.value, behavior.value)

    replace_unsupported_to = interp.Shape.TCB
    unsupported_occured = set()

    def generate_keys(keyframe_points):
        prev_kf = None
        for curr_kf in keyframe_points:
            shape = interp.Shape.STEPPED
            if prev_kf is not None:
                if prev_kf.interpolation == 'CONSTANT':
                    shape = interp.Shape.STEPPED
                elif prev_kf.interpolation == 'LINEAR':
                    shape = interp.Shape.LINEAR
                else:
                    unsupported_occured.add(prev_kf.interpolation)
                    shape = replace_unsupported_to
            prev_kf = curr_kf
            yield interp.KeyFrame(curr_kf.co.x / fps, curr_kf.co.y / koef, shape)

    kf_writer = rw.write.PackedWriter()
    keyframes = utilites.refine_keys(generate_keys(fcurve.keyframe_points), epsilon)
    count = write.export_keyframes(kf_writer, keyframes, anm_ver=ver)

    count_fmt = 'I'
    if ver > 3:
        count_fmt = 'H'
    writer.putf('<' + count_fmt, count)
    writer.putp(kf_writer)

    if unsupported_occured:
        log.warn(
            text.warn.envelope_shapes,
            shapes=unsupported_occured,
            replacement=replace_unsupported_to.name
        )
