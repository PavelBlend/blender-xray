# standart modules
import math
import time

# addon modules
from . import draw
from . import ie
from . import image
from . import obj
from . import material
from . import mesh
from . import action
from . import bone
from . import version
from . import stats
from . import tex
from .. import log
from .. import text


BAD_VTX_GROUP_NAME = '.xr-bad!'
_ADDON_VERSION_NUMBER = None
addon_version = None


def version_to_number(major, minor, release):
    return ((major & 0xff) << 24) | ((minor & 0xff) << 16) | (release & 0xffff)


def addon_version_number():
    global _ADDON_VERSION_NUMBER
    number = _ADDON_VERSION_NUMBER
    if number is None:
        number = version_to_number(*addon_version)
        _ADDON_VERSION_NUMBER = number
    return number


def smooth_euler(current, previous):
    for axis in range(3):
        current[axis] = _smooth_angle(current[axis], previous[axis])


def _smooth_angle(current, previous):
    delta = abs(current - previous)
    new_delta = (current - 2 * math.pi) - previous
    if abs(new_delta) < delta:
        return previous + new_delta
    new_delta = (current + 2 * math.pi) - previous
    if abs(new_delta) < delta:
        return previous + new_delta
    return current


def set_cursor_state(method):
    def wrapper(self, context, *args):
        context.window.cursor_set('WAIT')
        result = method(self, context, *args)
        context.window.cursor_set('DEFAULT')
        return result
    return wrapper


def time_log():
    def decorator(func):
        name = func.__name__
        def wrap(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                log.debug('time', func=name, time=time.time() - start)
        return wrap
    return decorator
