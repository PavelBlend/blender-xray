# addon modules
from . import const
from . import interp


def refine_keys(keyframes, eps=const.EPSILON):
    def significant(prev, curr, next_, skipped):
        def is_oor(key, derivative):
            expected_value = (key.time - prev.time) * derivative + prev.value
            return abs(expected_value - key.value) >= eps

        if prev is None:
            return curr is not None
        if curr.shape == next_.shape == interp.Shape.LINEAR:
            derivative = (next_.value - prev.value) / (next_.time - prev.time)
            if is_oor(curr, derivative):
                return True
            for key in skipped:
                if is_oor(key, derivative):
                    return True
            return False
        if abs(prev.value - curr.value) + abs(curr.value - next_.value) < eps:
            return False
        return True

    prev, curr = None, None    # preview keyframe, current keyframe
    skipped = []
    for next_ in keyframes:
        if significant(prev, curr, next_, skipped):
            skipped = []
            prev = curr
            yield curr
        elif curr is not None:
            skipped.append(curr)
        curr = next_

    if curr and ((not prev) or (abs(curr.value - prev.value) >= eps)):
        yield curr
