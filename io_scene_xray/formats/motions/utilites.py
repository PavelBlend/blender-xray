# addon modules
from . import interp


MOTIONS_FILTER_ALL = lambda name: True
EPSILON = 0.00001


def refine_keys(keyframes, epsilon=EPSILON):
    def significant(prev_kf, curr_kf, next_kf, skipped):
        def is_oor(keyframe, derivative):
            expected_value = (keyframe.time - prev_kf.time) * derivative + prev_kf.value
            return abs(expected_value - keyframe.value) >= epsilon

        if prev_kf is None:
            return curr_kf is not None
        if (curr_kf.shape == interp.Shape.LINEAR) and (next_kf.shape == interp.Shape.LINEAR):
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
