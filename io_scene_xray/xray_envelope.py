from enum import Enum
from .xray_io import PackedWriter
from .utils import mkstruct
from .log import warn, with_context
from . import xray_motions


class Behavior(Enum):
    RESET = 0
    CONSTANT = 1
    REPEAT = 2
    OSCILLATE = 3
    OFFSET_REPEAT = 4
    LINEAR = 5


class Shape(Enum):
    TCB = 0  # Kochanek-Bartels
    HERMITE = 1
    BEZIER_1D = 2  # obsolete, equivalent to HERMITE
    LINEAR = 3
    STEPPED = 4
    BEZIER_2D = 5


@with_context('import-envelope')
def import_envelope(reader, fcurve, fps, koef, name, warn_list, unique_shapes):
    bhv0, bhv1 = map(Behavior, reader.getf('<2B'))

    if bhv0 != bhv1:
        warn(
            'different behaviors, one will be replaced with another',
            behavior=bhv1.name,
            replacement=bhv0.name
        )
        bhv1 = bhv0
    if bhv0 == Behavior.CONSTANT:
        fcurve.extrapolation = 'CONSTANT'
    elif bhv0 == Behavior.LINEAR:
        fcurve.extrapolation = 'LINEAR'
    else:
        bhv1 = Behavior.CONSTANT
        warn(
            'behavior isn\'t supported, and will be replaced',
            behavior=bhv0.name,
            replacement=bhv1.name
        )
        bhv0 = bhv1
        fcurve.extrapolation = 'CONSTANT'

    replace_unsupported_to = 'BEZIER'
    unsupported_occured = set()
    fckf = fcurve.keyframe_points
    use_interpolate = False
    values = []
    times = []
    shapes = []
    tcb = []
    keyframes_count = reader.getf('<H')[0]
    for _ in range(keyframes_count):
        value = reader.getf('<f')[0]
        time = reader.getf('<f')[0] * fps
        shape = Shape(reader.getf('<B')[0])
        if shape != Shape.STEPPED:
            tension = reader.getq16f(-32.0, 32.0)
            continuity = reader.getq16f(-32.0, 32.0)
            bias = reader.getq16f(-32.0, 32.0)
            reader.getf('<4H')
        else:
            tension = None
            continuity = None
            bias = None
        values.append(value)
        times.append(time)
        shapes.append(shape)
        tcb.append((tension, continuity, bias))
        if not shape in (Shape.LINEAR, Shape.STEPPED, Shape.TCB):
            unsupported_occured.add(shape.name)
        unique_shapes.add(shape.name)
        if shape == Shape.TCB:
            use_interpolate = True
    if use_interpolate:
        start_frame = int(round(times[0], 0))
        end_frame = int(round(times[-1], 0))
        values, times = xray_motions.interpolate_keys(
            fps, start_frame, end_frame, values, times, shapes, tcb
        )
        for time, value in zip(times, values):
            key_frame = fckf.insert(time, value * koef)
            key_frame.interpolation = 'LINEAR'
    else:
        for time, value, shape in zip(times, values, shapes):
            key_frame = fckf.insert(time, value * koef)
            if shape == Shape.LINEAR:
                key_frame.interpolation = 'LINEAR'
            elif shape == Shape.STEPPED:
                key_frame.interpolation = 'CONSTANT'
            else:
                key_frame.interpolation = replace_unsupported_to

    if unsupported_occured:
        warn_list.append((
            tuple(unsupported_occured),
            replace_unsupported_to,
            name
        ))

    return use_interpolate


KF = mkstruct('KeyFrame', ['time', 'value', 'shape'])
EPSILON = 0.00001


@with_context('export-envelope')
def export_envelope(writer, fcurve, fps, koef, epsilon=EPSILON):
    behavior = None
    if fcurve.extrapolation == 'CONSTANT':
        behavior = Behavior.CONSTANT
    elif fcurve.extrapolation == 'LINEAR':
        behavior = Behavior.LINEAR
    else:
        behavior = Behavior.LINEAR
        warn(
            'Envelope: extrapolation is not supported, and will be replaced',
            extrapolation=fcurve.extrapolation,
            replacement=behavior.name
        )
    writer.putf('<2B', behavior.value, behavior.value)

    replace_unsupported_to = Shape.TCB
    unsupported_occured = set()

    def generate_keys(keyframe_points):
        prev_kf = None
        for curr_kf in keyframe_points:
            shape = Shape.STEPPED
            if prev_kf is not None:
                if prev_kf.interpolation == 'CONSTANT':
                    shape = Shape.STEPPED
                elif prev_kf.interpolation == 'LINEAR':
                    shape = Shape.LINEAR
                else:
                    unsupported_occured.add(prev_kf.interpolation)
                    shape = replace_unsupported_to
            prev_kf = curr_kf
            yield KF(curr_kf.co.x / fps, curr_kf.co.y / koef, shape)

    kf_writer = PackedWriter()
    keyframes = refine_keys(generate_keys(fcurve.keyframe_points), epsilon)
    count = export_keyframes(kf_writer, keyframes)

    writer.putf('<H', count)
    writer.putp(kf_writer)

    if unsupported_occured:
        warn(
            'Envelope: unsupported shapes will be replaced by',
            shapes=unsupported_occured,
            replacement=replace_unsupported_to.name
        )


def export_keyframes(writer, keyframes, time_end=None, fps=None):
    count = 0

    for keyframe in keyframes:
        count += 1
        writer.putf('<2f', keyframe.value, keyframe.time)
        writer.putf('<B', keyframe.shape.value)
        if keyframe.shape != Shape.STEPPED:
            writer.putf('<3H', 32768, 32768, 32768)
            writer.putf('<4H', 32768, 32768, 32768, 32768)

    # so that the animation doesn't change its length
    if not time_end is None:
        if (time_end - keyframe.time) > (1 / fps):
            writer.putf('<2f', keyframe.value, time_end)
            writer.putf('<B', Shape.STEPPED.value)
            count += 1

    return count


def refine_keys(keyframes, epsilon=EPSILON):
    def significant(prev_kf, curr_kf, next_kf, skipped):
        def is_oor(keyframe, derivative):
            expected_value = (keyframe.time - prev_kf.time) * derivative + prev_kf.value
            return abs(expected_value - keyframe.value) >= epsilon

        if prev_kf is None:
            return curr_kf is not None
        if (curr_kf.shape == Shape.LINEAR) and (next_kf.shape == Shape.LINEAR):
            derivative = (next_kf.value - prev_kf.value) / (next_kf.time - prev_kf.time)
            if is_oor(curr_kf, derivative):
                return True
            for keyframe in skipped:
                if is_oor(keyframe, derivative):
                    return True
            return False
        if (abs(prev_kf.value - curr_kf.value) + abs(curr_kf.value - next_kf.value)) < epsilon:
            return False
        return True

    prev_kf, curr_kf = None, None
    skipped = []
    for next_kf in keyframes:
        if significant(prev_kf, curr_kf, next_kf, skipped):
            skipped = []
            prev_kf = curr_kf
            yield curr_kf
        elif curr_kf is not None:
            skipped.append(curr_kf)
        curr_kf = next_kf

    if curr_kf and ((not prev_kf) or (abs(curr_kf.value - prev_kf.value) >= epsilon)):
        yield curr_kf
