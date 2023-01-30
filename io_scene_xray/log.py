# standart modules
import contextlib

# blender modules
import bpy

# addon modules
from . import text


CONTEXT_NAME = '@context'
__logger__ = None
__context__ = None


class AppError(Exception):
    def __init__(self, message, log_context=None):
        super().__init__(message)
        if log_context in None:
            log_context = props()
        self.log_context = log_context


class _LoggerContext:
    def __init__(self, data, parent=None, lightweight=False):
        self.data = data
        self.parent = parent
        self.lightweight = lightweight
        if parent:
            self.depth = (parent.depth + 1)
        else:
            self.depth = 0


class Logger:
    def __init__(self, report):
        self._report = report
        self._full = []

    def _format_message(self, message):
        message = str(message)
        message = text.get_text(message)
        message = message.strip()
        message = message[0].upper() + message[1: ]
        return message

    def _format_data(self, data):
        if CONTEXT_NAME in data:
            name = None
            args = []
            for key, val in data.items():
                if key is CONTEXT_NAME:
                    name = val
                else:
                    arg = '{0}={1}'.format(key, repr(val))
                    args.append(arg)
            args_str = ', '.join(args)
            result = '{0}({1})'.format(name, args_str)
            return result
        return str(data)

    def _message(self, message, message_type, ctx):
        message = self._format_message(message)
        self._full.append((message, ctx, message_type))

    def warn(self, message, ctx=None):
        self._message(message, 'WARNING', ctx)

    def err(self, message, ctx=None):
        self._message(message, 'ERROR', ctx)

    def flush(self, logname='log'):
        # collect message contexts
        uniq = dict()
        message_contexts = {}
        for msg, ctx, typ in self._full:
            count = uniq.get(msg, (0, typ))[0]
            uniq[msg] = count + 1, typ
            message_contexts.setdefault(msg, []).append(ctx.data)
        if not uniq:
            return

        # generate log lines and report
        lines = ['Digest:']
        for msg, (cnt, typ) in uniq.items():
            line = msg
            if cnt > 1:
                line = ' [{}x] '.format(cnt) + line
                lines.append(line)
            else:
                context_data = message_contexts[msg][0]
                if context_data:
                    prop = tuple(context_data.values())[0]
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
                    data = self._format_data(group.data)
                    line = '{}+-{}'.format(prefix, data)
                    lines.append(line)
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
                msg += (': {}'.format(data))
            if last_line_is_message and (last_message == msg):
                last_message_count += 1
                lines[-1] = '{}[{}x] {}'.format(
                    prefix,
                    last_message_count,
                    msg
                )
            else:
                lines.append(prefix + msg)
                last_message = msg
                last_message_count = 1
                last_line_is_message = True

        # create log text
        text_data = bpy.data.texts.new(logname)
        text_data.user_clear()
        text_data.from_string('\n'.join(lines))
        full_log_text = text.get_text(text.warn.full_log)
        self._report(
            {'WARNING'},
            full_log_text + ': "{}"'.format(text_data.name)
        )


def with_context(name=None):
    def decorator(func):
        def wrap(*args, **kwargs):
            global __context__
            saved = __context__
            try:
                __context__ = _LoggerContext({CONTEXT_NAME: name}, saved)
                return func(*args, **kwargs)
            finally:
                __context__ = saved
        return wrap
    return decorator


def update(**kwargs):
    __context__.data.update(**kwargs)


def props(**kwargs):
    return _LoggerContext(kwargs, __context__, True)


def warn(message, **kwargs):
    __logger__.warn(message, props(**kwargs))


def err(error):
    __logger__.err(str(error), error.log_context)


def debug(message, **kwargs):
    print('debug: %s: %s' % (message, kwargs))


def execute_with_logger(method):
    def wrapper(self, context):
        try:
            name = self.__class__.bl_idname.replace('.', '_')
            with logger(name, self.report):
                return method(self, context)
        except AppError:
            return {'CANCELLED'}

    return wrapper


@contextlib.contextmanager
def using_logger(logger_obj):
    global __logger__
    saved = __logger__
    try:
        __logger__ = logger_obj
        yield
    finally:
        __logger__ = saved


@contextlib.contextmanager
def logger(name, report):
    logger_obj = Logger(report)
    try:
        with using_logger(logger_obj):
            yield
    except AppError as err:
        logger_obj.err(str(err), err.log_context)
        raise err
    finally:
        logger_obj.flush(name)
