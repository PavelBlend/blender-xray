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


def _read_behavior(reader, ver):

    if ver > 3:
        bhv_fmt = 'B'
    else:
        bhv_fmt = 'I'

    bhv0, bhv1 = map(interp.Behavior, reader.getf('<2' + bhv_fmt))

    if bhv0 != bhv1:
        log.warn(
            text.warn.envelope_behaviors_replaced,
            behavior=bhv1.name,
            replacement=bhv0.name
        )
        bhv1 = bhv0

    return bhv0


def _set_behavior(fcurve, behavior):

    if behavior == interp.Behavior.CONSTANT:
        fcurve.extrapolation = 'CONSTANT'

    elif behavior == interp.Behavior.LINEAR:
        fcurve.extrapolation = 'LINEAR'

    else:
        fcurve.extrapolation = 'CONSTANT'

        log.warn(
            text.warn.envelope_bad_behavior,
            behavior=behavior.name,
            replacement=interp.Behavior.CONSTANT.name
        )

def _import_behavior(reader, ver, fcurve):
    # behavior is similar to extrapolation in blender

    behavior = _read_behavior(reader, ver)
    _set_behavior(fcurve, behavior)


def _read_frames_new_format(
        reader,
        fps,
        unique_shapes,
        values,
        times,
        shapes,
        tcb,
        params
    ):

    use_interpolate = False

    keyframes_count = reader.getf('<H')[0]

    for _ in range(keyframes_count):
        value = reader.getf('<f')[0]
        time = reader.getf('<f')[0] * fps
        shape = interp.Shape(reader.getf('<B')[0])

        if shape == interp.Shape.STEPPED:
            tension = 0.0
            continuity = 0.0
            bias = 0.0
            param = (0.0, 0.0, 0.0, 0.0)

        else:
            tension = reader.getq16f(-32.0, 32.0)
            continuity = reader.getq16f(-32.0, 32.0)
            bias = reader.getq16f(-32.0, 32.0)
            param = (
                reader.getq16f(-32.0, 32.0),
                reader.getq16f(-32.0, 32.0),
                reader.getq16f(-32.0, 32.0),
                reader.getq16f(-32.0, 32.0)
            )

        values.append(value)
        times.append(time)
        shapes.append(shape)
        tcb.append((tension, continuity, bias))
        params.append(param)

        unique_shapes.add(shape.name)

        if shape not in (interp.Shape.STEPPED, interp.Shape.LINEAR):
            use_interpolate = True

    return use_interpolate


def _read_frames_old_format(
        reader,
        fps,
        unique_shapes,
        values,
        times,
        shapes,
        tcb,
        params
    ):

    use_interpolate = False

    keyframes_count = reader.getf('<I')[0]

    for _ in range(keyframes_count):
        value = reader.getf('<f')[0]
        time = reader.getf('<f')[0] * fps
        shape = interp.Shape(reader.uint32() & 0xff)
        tension, continuity, bias = reader.getf('<3f')
        param = reader.getf('<4f')

        values.append(value)
        times.append(time)
        shapes.append(shape)
        tcb.append((tension, continuity, bias))
        params.append(param)

        unique_shapes.add(shape.name)

        if shape not in (interp.Shape.STEPPED, interp.Shape.LINEAR):
            use_interpolate = True

    return use_interpolate


def _insert_keyframes_interp(
        fcurve,
        koef,
        values,
        times,
        shapes,
        tcb,
        params
    ):

    start_frame = int(round(times[0], 0))
    end_frame = int(round(times[-1], 0))

    values, times = imp.interpolate_keys(
        start_frame,
        end_frame,
        values,
        times,
        shapes,
        tcb,
        params
    )

    frames_coords = []

    for time, value in zip(times, values):
        frames_coords.extend((time, value * koef))

    utils.action.insert_keyframes_for_single_curve(frames_coords, fcurve)


def _insert_keyframes_raw(
        fcurve,
        koef,
        values,
        times,
        shapes
    ):

    key_count = len(times)
    interps = []
    frames_coords = []

    for index, (time, value) in enumerate(zip(times, values)):
        frames_coords.extend((time, value * koef))

        if index + 1 < key_count:
            shape = shapes[index + 1]
        else:
            shape = shapes[-1]

        if shape == interp.Shape.LINEAR:
            interps.append('LINEAR')
        else:
            interps.append('CONSTANT')

    utils.action.insert_keyframes_for_single_curve(
        frames_coords,
        fcurve,
        interps=interps
    )


def _insert_keyframes(
        fcurve,
        koef,
        values,
        times,
        shapes,
        tcb,
        params,
        use_interp
    ):

    # insert TCB, Hermite, Bezier 1D, Bezier 2D keyframes
    if use_interp:
        _insert_keyframes_interp(
            fcurve,
            koef,
            values,
            times,
            shapes,
            tcb,
            params
        )

    # insert Stepped, Linear keyframes
    else:
        _insert_keyframes_raw(fcurve, koef, values, times, shapes)


def _read_frames(reader, ver, fps, unique_shapes):
    values = []
    times = []
    shapes = []
    tcb = []
    params = []

    if ver > 3:
        use_interp = _read_frames_new_format(
            reader,
            fps,
            unique_shapes,
            values,
            times,
            shapes,
            tcb,
            params
        )

    else:
        use_interp = _read_frames_old_format(
            reader,
            fps,
            unique_shapes,
            values,
            times,
            shapes,
            tcb,
            params
        )

    return values, times, shapes, tcb, params, use_interp


def _import_frames(reader, ver, fcurve, fps, koef, unique_shapes):

    values, times, shapes, tcb, params, use_interp = _read_frames(
        reader,
        ver,
        fps,
        unique_shapes
    )

    _insert_keyframes(
        fcurve,
        koef,
        values,
        times,
        shapes,
        tcb,
        params,
        use_interp
    )

    return use_interp


@log.with_context('envelope')
def import_envelope(reader, ver, fcurve, fps, koef, shapes):

    _import_behavior(reader, ver, fcurve)
    use_interp = _import_frames(reader, ver, fcurve, fps, koef, shapes)

    return use_interp


@log.with_context('envelope')
def export_envelope(writer, ver, act, fcurve, fps, koef, epsilon=const.EPSILON):
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

    if ver > 3:
        behav_fmt = 'B'
    else:
        behav_fmt = 'I'

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

    frame_start, frame_end = act.frame_range
    time_end = (frame_end - frame_start) / fps

    kf_writer = rw.write.PackedWriter()
    keyframes = utilites.refine_keys(generate_keys(fcurve.keyframe_points), epsilon)
    count = write.export_keyframes(kf_writer, keyframes, fps, time_end, ver)

    if ver > 3:
        count_fmt = 'H'
    else:
        count_fmt = 'I'

    writer.putf('<' + count_fmt, count)
    writer.putp(kf_writer)

    if unsupported_occured:
        log.warn(
            text.warn.envelope_shapes,
            shapes=unsupported_occured,
            replacement=replace_unsupported_to.name
        )
