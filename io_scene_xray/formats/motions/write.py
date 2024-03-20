# standart modules
import struct

# addon modules
from . import interp


HNDL_INT = 32768    # default integer coordinate for keyframe handle
HNDL_FLT = 0.0    # default float coordinate for keyframe handle


def export_keyframes(writer, keyframes, fps, time_end, anm_ver):
    count = 0

    if anm_ver == 3:
        params_default = HNDL_FLT
        params_format = 'f'
        shape_format = '<I'

    else:
        params_default = HNDL_INT
        params_format = 'H'
        shape_format = '<B'

    # 7 values - tension, continuity, bias,
    # x, y coordinates for left and right handles
    params = (params_default, ) * 7
    params_data = struct.pack('<7' + params_format, *params)

    # version 3
    if anm_ver == 3:

        for keyframe in keyframes:
            count += 1

            writer.putf('<2f', keyframe.value, keyframe.time)
            writer.putf(shape_format, keyframe.shape.value & 0xff)

            writer.data.extend(params_data)

    # version 4 and 5
    else:

        for keyframe in keyframes:
            count += 1

            writer.putf('<2f', keyframe.value, keyframe.time)
            writer.putf(shape_format, keyframe.shape.value)

            if keyframe.shape != interp.Shape.STEPPED:
                writer.data.extend(params_data)

    # so that the animation doesn't change its length
    if time_end is not None:
        if (time_end - keyframe.time) > (1 / fps):

            writer.putf('<2f', keyframe.value, time_end)
            writer.putf(shape_format, interp.Shape.STEPPED.value)

            if anm_ver == 3:
                writer.data.extend(params_data)

            count += 1

    return count
