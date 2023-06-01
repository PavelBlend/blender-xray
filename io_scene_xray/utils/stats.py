# standart modules
import time

# blender modules
import bpy


statistics = None
STATS_FILE_NAME = 'xray_stats'
HISTORY_FILE_NAME = 'xray_stats_history'


class Statistics:
    def __init__(self):
        self.lines = []
        self.context = ''
        self.date = time.strftime('%Y.%m.%d %H:%M:%S')

        self.start_time = None
        self.end_time = None

        self.global_start_time = None
        self.global_end_time = None

    def info(self, data):
        self.lines.append(data)

    def create_bpy_text(self):
        date_info = 'started {0}: {1}\n\n'.format(self.context, self.date)
        info_str = date_info + '\n'.join(self.lines)

        # get history text
        text_history = bpy.data.texts.get(HISTORY_FILE_NAME)
        if not text_history:
            text_history = bpy.data.texts.new(HISTORY_FILE_NAME)
            text_history.user_clear()

        # get statistics text
        text_stats = bpy.data.texts.get(STATS_FILE_NAME)
        if not text_stats:
            text_stats = bpy.data.texts.new(STATS_FILE_NAME)
            text_stats.user_clear()

        # write statistics text
        text_stats.from_string(info_str)

        # write history text
        stats_data = text_stats.as_string()
        history_data = text_history.as_string()

        separator = '\n' + '-'*100

        if history_data:
            history = history_data + '\n'*4 + stats_data + separator
        else:
            history = stats_data + separator

        text_history.from_string(history)

    def flush(self):
        self.create_bpy_text()


def update(context):
    global statistics
    statistics.context = context


def info(data):
    global statistics
    statistics.info(data)


def start_time():
    global statistics
    statistics.start_time = time.time()


def end_time():
    global statistics
    statistics.end_time = time.time()


def total_time(message, is_global=False):
    global statistics

    if is_global:
        total_time = statistics.global_end_time - statistics.global_start_time
    else:
        total_time = statistics.end_time - statistics.start_time

    total_time_str = '{0:.3f} sec'.format(total_time)
    total_time_message = '{0}: {1}'.format(message, total_time_str)
    info(total_time_message)


def execute_with_stats(method):

    def wrapper(self, context):
        global statistics

        # before executing
        statistics = Statistics()
        statistics.global_start_time = time.time()

        result = method(self, context)

        # after executing
        statistics.global_end_time = time.time()
        total_time('\ntotal time', is_global=True)
        statistics.flush()
        statistics = None

        return result

    return wrapper
