# standart modules
import enum


class Behavior(enum.Enum):
    RESET = 0
    CONSTANT = 1
    REPEAT = 2
    OSCILLATE = 3
    OFFSET_REPEAT = 4
    LINEAR = 5


class Shape(enum.Enum):
    TCB = 0    # Kochanek-Bartels
    HERMITE = 1
    BEZIER_1D = 2    # obsolete, equivalent to HERMITE
    LINEAR = 3
    STEPPED = 4
    BEZIER_2D = 5


class KeyFrame:
    def __init__(self, time, value, shape):
        self.time = time
        self.value = value
        self.shape = shape


class Key:
    def __init__(self):
        self.value = None
        self.time = None
        self.shape = None
        self.tension = None
        self.cont = None    # continuity
        self.bias = None
        self.param_1 = None
        self.param_2 = None
        self.param_3 = None
        self.param_4 = None


def incoming(start, end, next_):
    if end.shape == Shape.TCB:
        a = (1.0 - end.tension) * (1.0 - end.cont) * (1.0 + end.bias)
        b = (1.0 - end.tension) * (1.0 + end.cont) * (1.0 - end.bias)
        d = end.value - start.value
        if next_.time is not None:
            t = (end.time - start.time) / (next_.time - start.time)
            in_ = t * (b * (next_.value - end.value) + a * d)
        else:
            in_ = 0.5 * (a + b) * d
    elif end.shape == Shape.LINEAR:
        in_ = (end.value - start.value) / (end.time - start.time)
    elif end.shape in (Shape.HERMITE, Shape.BEZIER_1D):
        in_ = end.param_1
        if next_.time is not None:
            in_ *= (end.time - start.time) / (next_.time - start.time)
    else:
        in_ = 0.0
    return in_


def outgoing(start, end, prev):
    if start.shape == Shape.TCB:
        a = (1.0 - start.tension) * (1.0 + start.cont) * (1.0 + start.bias)
        b = (1.0 - start.tension) * (1.0 - start.cont) * (1.0 - start.bias)
        d = end.value - start.value
        if prev.time is not None:
            t = (end.time - start.time) / (end.time - prev.time)
            out = t * (a * (start.value - prev.value) + b * d)
        else:
            out = 0.5 * (a + b) * d
    elif start.shape in (Shape.HERMITE, Shape.BEZIER_1D):
        out = start.param_2
        if prev.time is not None:
            out *= (end.time - start.time) / (end.time - prev.time)
    else:
        out = 0.0
    return out


def hermite(t):    # t - time
    t2 = t * t    # time square
    t3 = t * t2    # time cubic
    h2 = 3.0 * t2 - t3 - t3    # hermite basis 2
    h1 = 1.0 - h2    # hermite basis 1
    h4 = t3 - t2    # hermite basis 4
    h3 = h4 - t2 + t    # hermite basis 3
    return h1, h2, h3, h4


def bezier(x0, x1, x2, x3, t):
    t2 = t * t
    t3 = t2 * t
    c = 3.0 * (x1 - x0)
    b = 3.0 * (x2 - x1) - c
    a = x3 - x0 - c - b
    return a * t3 + b * t2 + c * t + x0


def bez2_time(x0, x1, x2, x3, time, t0, t1):
    t = t0 + (t1 - t0) * 0.5
    v = bezier(x0, x1, x2, x3, t)
    if abs(time - v) > 0.0001:
        if v > time:
            t1 = t
        else:
            t0 = t
        return bez2_time(x0, x1, x2, x3, time, t0, t1)
    else:
        return t


def bezier_2d(time, start, end, prev_key):
    if start.shape == Shape.BEZIER_2D:
        x = start.time + start.param_3
    else:
        x = start.time + (end.time - start.time) / 3
    t = bez2_time(
        start.time, x,
        end.time + end.param_1,
        end.time,
        time,
        0.0,
        1.0
    )
    if start.shape == Shape.BEZIER_2D:
        y = start.value + start.param_4
    else:
        y = start.value + outgoing(start, end, prev_key) / 3
    res = bezier(start.value, y, end.param_2 + end.value, end.value, t)
    return res


def evaluate(time, start_key, end_key, prev_key, next_key):
    if time == start_key.time:
        return start_key.value
    elif time == end_key.time:
        return end_key.value
    # normalized time in [0, 1]
    time_norm = (time - start_key.time) / (end_key.time - start_key.time)
    if end_key.shape in (Shape.TCB, Shape.HERMITE, Shape.BEZIER_1D):
        out = outgoing(start_key, end_key, prev_key)
        in_ = incoming(start_key, end_key, next_key)
        h1, h2, h3, h4 = hermite(time_norm)    # hermite basics
        return h1 * start_key.value + h2 * end_key.value + h3 * out + h4 * in_
    elif end_key.shape == Shape.BEZIER_2D:
        return bezier_2d(time, start_key, end_key, prev_key)
    elif end_key.shape == Shape.LINEAR:
        return start_key.value + time_norm * (end_key.value - start_key.value)
    elif end_key.shape == Shape.STEPPED:
        return start_key.value
