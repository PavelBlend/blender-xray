# addon modules
from . import utils
from . import xray_interpolation


KF = utils.mkstruct('KeyFrame', ['time', 'value', 'shape'])
EPSILON = 0.00001


def export_keyframes(writer, keyframes, time_end=None, fps=None, anm_ver=5):
    count = 0

    if anm_ver > 3:
        for keyframe in keyframes:
            count += 1
            writer.putf('<2f', keyframe.value, keyframe.time)
            writer.putf('<B', keyframe.shape.value)
            if keyframe.shape != xray_interpolation.Shape.STEPPED:
                writer.putf('<3H', 32768, 32768, 32768)
                writer.putf('<4H', 32768, 32768, 32768, 32768)

        # so that the animation doesn't change its length
        if not time_end is None:
            if (time_end - keyframe.time) > (1 / fps):
                writer.putf('<2f', keyframe.value, time_end)
                writer.putf('<B', xray_interpolation.Shape.STEPPED.value)
                count += 1

    else:
        for keyframe in keyframes:
            count += 1
            writer.putf('<2f', keyframe.value, keyframe.time)
            writer.putf('<I', keyframe.shape.value & 0xff)
            writer.putf('<3f', 0.0, 0.0, 0.0)    # TCB
            writer.putf('<4f', 0.0, 0.0, 0.0, 0.0)

        # so that the animation doesn't change its length
        if not time_end is None:
            if (time_end - keyframe.time) > (1 / fps):
                writer.putf('<2f', keyframe.value, time_end)
                writer.putf('<I', xray_interpolation.Shape.STEPPED.value)
                count += 1

    return count


def refine_keys(keyframes, epsilon=EPSILON):
    def significant(prev_kf, curr_kf, next_kf, skipped):
        def is_oor(keyframe, derivative):
            expected_value = (keyframe.time - prev_kf.time) * derivative + prev_kf.value
            return abs(expected_value - keyframe.value) >= epsilon

        if prev_kf is None:
            return curr_kf is not None
        if (curr_kf.shape == xray_interpolation.Shape.LINEAR) and (next_kf.shape == xray_interpolation.Shape.LINEAR):
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
