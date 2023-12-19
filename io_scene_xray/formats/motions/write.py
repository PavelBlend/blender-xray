# addon modules
from . import interp


def export_keyframes(writer, keyframes, time_end=None, fps=None, anm_ver=5):
    count = 0

    if anm_ver > 3:
        for keyframe in keyframes:
            count += 1
            writer.putf('<2f', keyframe.value, keyframe.time)
            writer.putf('<B', keyframe.shape.value)
            if keyframe.shape != interp.Shape.STEPPED:
                writer.putf('<3H', 32768, 32768, 32768)
                writer.putf('<4H', 32768, 32768, 32768, 32768)

        # so that the animation doesn't change its length
        if time_end is not None:
            if (time_end - keyframe.time) > (1 / fps):
                writer.putf('<2f', keyframe.value, time_end)
                writer.putf('<B', interp.Shape.STEPPED.value)
                count += 1

    else:
        for keyframe in keyframes:
            count += 1
            writer.putf('<2f', keyframe.value, keyframe.time)
            writer.putf('<I', keyframe.shape.value & 0xff)
            writer.putf('<3f', 0.0, 0.0, 0.0)    # TCB
            writer.putf('<4f', 0.0, 0.0, 0.0, 0.0)

        # so that the animation doesn't change its length
        if time_end is not None:
            if (time_end - keyframe.time) > (1 / fps):
                writer.putf('<2f', keyframe.value, time_end)
                writer.putf('<I', interp.Shape.STEPPED.value)
                count += 1

    return count
