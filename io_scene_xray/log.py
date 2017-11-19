from contextlib import contextmanager

# Context Handling
CTX_NAME = '@context'
__ctx__ = [None]

def with_context(name=None):
    def decorator(func):
        def wrap(*args, **kwargs):
            saved = __ctx__[0]
            try:
                __ctx__[0] = _Ctx({CTX_NAME:name}, saved)
                return func(*args, **kwargs)
            finally:
                __ctx__[0] = saved
        return wrap
    return decorator

def update(**kwargs):
    __ctx__[0].data.update(**kwargs)

def props(**kwargs):
    return _Ctx(kwargs, __ctx__[0], True)


# Logging

__logger__ = [None]

def warn(message, **kwargs):
    __logger__[0].warn(message, props(**kwargs))

def debug(message, **kwargs):
    print('debug: %s: %s' % (message, kwargs))

@contextmanager
def using_logger(logger):
    saved = __logger__[0]
    try:
        __logger__[0] = logger
        yield
    finally:
        __logger__[0] = saved


# Implementation

class _Ctx:
    def __init__(self, data, parent=None, lightweight=False):
        self.data = data
        self.parent = parent
        self.depth = (parent.depth + 1) if parent else 0
        self.lightweight = lightweight
