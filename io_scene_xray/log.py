# standart modules
import contextlib

# blender modules
import bpy

# addon modules
from . import text


LOG_FILE_NAME = 'xray_log'
HISTORY_FILE_NAME = 'xray_log_history'
CONTEXT_NAME = '@context'
_logger = None
_context = None
create_bpy_text = True
general_log = None


class AppError(Exception):
    def __init__(self, message, log_context=None):
        super().__init__(message)
        if log_context is None:
            log_context = props()
        self.log_context = log_context


class _LoggerContext:
    def __init__(self, data, parent=None, lightweight=False):
        self.data = data
        self.parent = parent
        self.lightweight = lightweight
        if parent:
            self.depth = parent.depth + 1
        else:
            self.depth = 0


class Logger:
    def __init__(self, report):
        self._report = report
        self._full = []

    def _format_message(self, message):
        message = str(message)
        message = text.get_text(message)
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

    def _collect_contexts(self):
        # collect message contexts
        self.messages_count = {}
        self.messages_type = {}
        self.messages_context = {}

        for message, context, message_type in self._full:
            count = self.messages_count.get(message, 0)
            self.messages_count[message] = count + 1
            self.messages_type[message] = message_type
            self.messages_context.setdefault(message, []).append(context.data)

        return bool(self.messages_count)

    def _init_log(self):
        self.lines = []
        self.processed_groups = {}
        self.last_line_is_message = False

    def _generate_short_log(self):
        # generate short log lines and report messages
        self.lines.append('Digest:')

        for message, count in self.messages_count.items():
            message_type = self.messages_type[message]
            line = message

            if count > 1:
                line = '[{0}x] {1}'.format(count, line)
                self.lines.append(' ' + line)

            else:
                context_data = self.messages_context[message][0]

                if context_data:
                    prop = tuple(context_data.values())[0]
                    if line.endswith('.'):
                        line = line[ : -1]
                    self.lines.append(' ' + line)
                    line = '{0}: "{1}"'.format(line, prop)

                else:
                    self.lines.append(' ' + line)

            # report
            self._report({message_type}, line)

    def _ensure_group_processed(self, group):
        prefix = self.processed_groups.get(group, None)
        if prefix is None:
            if group is not None:
                if group.parent:
                    self._ensure_group_processed(group.parent)
                prefix = '| ' * group.depth
                if self.last_line_is_message:
                    self.lines.append(prefix + '|')
                data = self._format_data(group.data)
                line = '{}+-{}'.format(prefix, data)
                self.lines.append(line)
                self.last_line_is_message = False
                prefix += '|  '
            else:
                prefix = ''
            self.processed_groups[group] = prefix
        return prefix

    def _generate_full_log(self):
        self.lines.extend(['', 'Full log:'])
        last_message = None
        last_message_count = 0

        for message, context, _ in self._full:
            data = {}
            group = context

            while group and group.lightweight:
                data.update(group.data)
                group = group.parent

            prefix = self._ensure_group_processed(group)

            if data:
                if message.endswith('.'):
                    message = message[ : -1]
                message += (': {}'.format(data))

            if self.last_line_is_message and (last_message == message):
                last_message_count += 1
                self.lines[-1] = '{}[{}x] {}'.format(
                    prefix,
                    last_message_count,
                    message
                )

            else:
                self.lines.append(prefix + message)
                last_message = message
                last_message_count = 1
                self.last_line_is_message = True

    def _create_bpy_text(self):
        if create_bpy_text:
            log_str = '\n'.join(self.lines)

            # get log text
            text_log = bpy.data.texts.get(LOG_FILE_NAME)
            if not text_log:
                text_log = bpy.data.texts.new(LOG_FILE_NAME)
                text_log.user_clear()

            # get log history text
            text_history = bpy.data.texts.get(HISTORY_FILE_NAME)
            if not text_history:
                text_history = bpy.data.texts.new(HISTORY_FILE_NAME)
                text_history.user_clear()

            # write log
            text_log.from_string(log_str)

            # write log history
            log_data = text_log.as_string()
            history_data = text_history.as_string()

            separator = '\n' + '-'*100

            if history_data:
                history = history_data + '\n'*4 + log_data + separator
            else:
                history = log_data + separator

            text_history.from_string(history)

            # report info
            full_log_text = text.get_text(text.warn.full_log)
            self._report(
                {'WARNING'},
                '{0}: "{1}"'.format(full_log_text, text_log.name)
            )

    def flush(self, is_last_flush=False):
        has_massages = self._collect_contexts()

        generate_log = False
        if has_massages:
            if general_log:
                if is_last_flush:
                    generate_log = True
            else:
                generate_log = True

        if generate_log:
            self._init_log()
            self._generate_short_log()
            self._generate_full_log()
            self._create_bpy_text()


def update(**kwargs):
    _context.data.update(**kwargs)


def props(**kwargs):
    return _LoggerContext(kwargs, _context, True)


def warn(message, **kwargs):
    _logger.warn(message, props(**kwargs))


def err(error):
    _logger.err(str(error), error.log_context)


def debug(message, **kwargs):
    # do not print warnings during automated tests
    if not bpy.app.background:
        print('debug: {}: {}'.format(message, kwargs))


def set_logger(logger):
    global _logger
    _logger = logger


def with_context(name=None):

    def decorator(func):

        def wrap(*args, **kwargs):
            global _context
            saved = _context
            try:
                _context = _LoggerContext({CONTEXT_NAME: name}, saved)
                return func(*args, **kwargs)
            finally:
                _context = saved

        return wrap

    return decorator


def execute_with_logger(method):

    def wrapper(self, context):
        try:
            with logger(self.report):
                return method(self, context)

        except AppError:
            return {'CANCELLED'}

    return wrapper


@contextlib.contextmanager
def using_logger(logger_obj):
    global _logger
    saved = _logger

    try:
        _logger = logger_obj
        yield

    finally:
        _logger = saved


@contextlib.contextmanager
def logger(report):
    if general_log:
        logger_obj = general_log
    else:
        logger_obj = Logger(report)

    try:
        with using_logger(logger_obj):
            yield

    except AppError as error:
        logger_obj.err(str(error), error.log_context)
        raise error

    finally:
        logger_obj.flush()
