# standart modules
import contextlib

# blender modules
import bpy

# addon modules
from . import text


# Context Handling
CTX_NAME = '@context'
__ctx__ = [None]


class AppError(Exception):
    def __init__(self, message, ctx=None):
        if ctx is None:
            ctx = props()
        super().__init__(message)
        self.ctx = ctx


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


def err(error):
    __logger__[0].err(str(error), error.ctx)


def debug(message, **kwargs):
    print('debug: %s: %s' % (message, kwargs))


@contextlib.contextmanager
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


class Logger:
    def __init__(self, report):
        self._report = report
        self._full = list()

    def message_format(self, message):
        message = str(message)
        message = text.get_text(message)
        message = message.strip()
        message = message[0].upper() + message[1:]
        return message

    def warn(self, message, ctx=None):
        message = self.message_format(message)
        self._full.append((message, ctx, 'WARNING'))

    def err(self, message, ctx=None):
        message = self.message_format(message)
        self._full.append((message, ctx, 'ERROR'))

    def flush(self, logname='log'):
        uniq = dict()
        message_contexts = {}
        for msg, ctx, typ in self._full:
            uniq[msg] = uniq.get(msg, (0, typ))[0] + 1, typ
            message_contexts.setdefault(msg, []).append(ctx.data)
        if not uniq:
            return

        lines = ['Digest:']
        for msg, (cnt, typ) in uniq.items():
            line = msg
            if cnt > 1:
                line = ('[%dx] ' % cnt) + line
                lines.append(' ' + line)
            else:
                context = message_contexts[msg]
                if context[0]:
                    prop = tuple(context[0].values())[0]
                    if line.endswith('.'):
                        line = line[ : -1]
                    lines.append(' ' + line)
                    line = '{0}: "{1}"'.format(line, prop)
                else:
                    lines.append(' ' + line)
            self._report({typ}, line)

        lines.extend(['', 'Full log:'])
        processed_groups = dict()
        last_line_is_message = False

        def fmt_data(data):
            if CTX_NAME in data:
                name = None
                args = []
                for key, val in data.items():
                    if key is CTX_NAME:
                        name = val
                    else:
                        args.append('%s=%s' % (key, repr(val)))
                return '%s(%s)' % (name, ', '.join(args))
            return str(data)

        def ensure_group_processed(group):
            nonlocal last_line_is_message
            prefix = processed_groups.get(group, None)
            if prefix is None:
                if group is not None:
                    if group.parent:
                        ensure_group_processed(group.parent)
                    prefix = '| ' * group.depth
                    if last_line_is_message:
                        lines.append(prefix + '|')
                    lines.append('%s+-%s' % (prefix, fmt_data(group.data)))
                    last_line_is_message = False
                    prefix += '|  '
                else:
                    prefix = ''
                processed_groups[group] = prefix
            return prefix


        last_message = None
        last_message_count = 0
        for msg, ctx, typ in self._full:
            data = dict()
            group = ctx
            while group and group.lightweight:
                data.update(group.data)
                group = group.parent
            prefix = ensure_group_processed(group)
            if data:
                if msg.endswith('.'):
                    msg = msg[ : -1]
                msg += (': %s' % data)
            if last_line_is_message and (last_message == msg):
                last_message_count += 1
                lines[-1] = '%s[%dx] %s' % (prefix, last_message_count, msg)
            else:
                lines.append(prefix + msg)
                last_message = msg
                last_message_count = 1
                last_line_is_message = True

        text_data = bpy.data.texts.new(logname)
        text_data.user_clear()
        text_data.from_string('\n'.join(lines))
        self._report(
            {'WARNING'},
            text.warn.full_log.format(text_data.name)
        )


@contextlib.contextmanager
def logger(name, report):
    lgr = Logger(report)
    try:
        with using_logger(lgr):
            yield
    except AppError as err:
        lgr.err(str(err), err.ctx)
        raise err
    finally:
        lgr.flush(name)


def execute_with_logger(method):
    def wrapper(self, context):
        try:
            name = self.__class__.bl_idname.replace('.', '_')
            with logger(name, self.report):
                return method(self, context)
        except AppError:
            return {'CANCELLED'}

    return wrapper
