from contextlib import contextmanager

# Context Handling
_ctx = None

def with_context(name=None):
    def decorator(func):
        def wrap(*args, **kwargs):
            global _ctx
            saved = _ctx
            try:
                _ctx = LogContext({'@type':name}, _ctx)
                return func(*args, **kwargs)
            finally:
                _ctx = saved
        return wrap
    return decorator

def update(**kwargs):
    _ctx.data.update(**kwargs)

def props(**kwargs):
    return LogContext(kwargs, _ctx, True)


# Logging

_logger = None

def warn(message, **kwargs):
    _logger.warn(message, props(**kwargs))

@contextmanager
def using_logger(logger):
    global _logger
    saved = _logger
    try:
        _logger = logger
        yield
    finally:
        _logger = saved


# Implementation

class LogContext:
    def __init__(self, data=dict(), parent=None, lightweight=False):
        self.data = data
        self.parent = parent
        self.depth = (parent.depth + 1) if parent else 0
        self.lightweight = lightweight
