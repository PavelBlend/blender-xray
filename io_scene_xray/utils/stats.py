# standart modules
import time

# blender modules
import bpy

# addon modules
from . import version


statistics = None
STATS_FILE_NAME = 'xray_stats'
HISTORY_FILE_NAME = 'xray_stats_history'


class Statistics:
    def __init__(self):
        self.lines = []
        self.files_count = 0
        self.status = ''
        self.context = ''
        self.time_stage = None
        self.stage_name = None
        self.date = time.strftime('%Y.%m.%d %H:%M:%S')

        self.objs_count = 0
        self.mshs_count = 0
        self.arms_count = 0
        self.mats_count = 0
        self.texs_count = 0
        self.imgs_count = 0
        self.acts_count = 0

        self.props = None
        self.print_status = version.get_preferences().use_batch_status

    def info(self, data):
        self.lines.append(data)

    def create_bpy_text(self):
        date_info = 'Started {0}: {1}\n\n'.format(self.context, self.date)
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


def created_obj():
    global statistics
    if statistics:
        statistics.objs_count += 1


def created_msh():
    global statistics
    if statistics:
        statistics.mshs_count += 1


def created_arm():
    global statistics
    if statistics:
        statistics.arms_count += 1


def created_mat():
    global statistics
    if statistics:
        statistics.mats_count += 1


def created_tex():
    global statistics
    if statistics:
        statistics.texs_count += 1


def created_img():
    global statistics
    if statistics:
        statistics.imgs_count += 1


def created_act():
    global statistics
    if statistics:
        statistics.acts_count += 1


def status(status_str, *props):
    global statistics
    if statistics:
        statistics.status = status_str
        statistics.props = props

        if statistics.print_status:
            file_path = props[0]
            print(file_path)


def stage(stage_name):
    global statistics
    if statistics:
        statistics.stage_name = stage_name


def update(context):
    global statistics
    if statistics:
        statistics.context = context


def info(data):
    global statistics
    if statistics:
        statistics.info(data)


def normalize_time(time_sec):
    if time_sec <= 60:
        norm_time = '{0:.3f} sec'.format(time_sec)

    else:
        mins = int(time_sec // 60)
        secs = time_sec % 60
        norm_time = '{0:d} min {1:.3f} sec'.format(mins, secs)

    return norm_time


def end_time(start_time):
    global statistics

    end_time = time.time()
    total_time = end_time - start_time

    total_time_str = normalize_time(total_time)

    if statistics.props:
        file_path = statistics.props[0]

        if statistics.time_stage:
            time_stage_str = normalize_time(statistics.time_stage)
            others_time_str = normalize_time(
                total_time - statistics.time_stage
            )
            total_time_message = '{0} {1:>12} ({2}: {3:>12}, Others: {4:>12}): "{5}"'.format(
                statistics.status,
                total_time_str,
                statistics.stage_name,
                time_stage_str,
                others_time_str,
                file_path
            )

        else:
            total_time_message = '{0} {1:>12}: "{2}"'.format(
                statistics.status,
                total_time_str,
                file_path
            )

    else:
        total_time_message = '{0}: {1}'.format(
            statistics.status,
            total_time_str
        )

    statistics.time_stage = None
    info(total_time_message)


def data_blocks_count_info():
    global statistics

    if statistics.context.split(' ')[0] == 'Export':
        return

    info('Created:')

    if statistics.objs_count:
        objs_count = '    Objects: {}'.format(statistics.objs_count)
        info(objs_count)

    if statistics.mshs_count:
        mshs_count = '    Meshes: {}'.format(statistics.mshs_count)
        info(mshs_count)

    if statistics.arms_count:
        arms_count = '    Armatures: {}'.format(statistics.arms_count)
        info(arms_count)

    if statistics.mats_count:
        mats_count = '    Materials: {}'.format(statistics.mats_count)
        info(mats_count)

    if statistics.texs_count:
        texs_count = '    Textures: {}'.format(statistics.texs_count)
        info(texs_count)

    if statistics.imgs_count:
        imgs_count = '    Images: {}'.format(statistics.imgs_count)
        info(imgs_count)

    if statistics.acts_count:
        acts_count = '    Actions: {}'.format(statistics.acts_count)
        info(acts_count)


def timer(method):

    def wrapper(*args, **kwargs):
        global statistics

        # before executing
        start_time = time.time()

        result = method(*args, **kwargs)

        # after executing
        end_time(start_time)
        statistics.files_count += 1

        return result

    return wrapper


def timer_stage(method):

    def wrapper(*args, **kwargs):
        global statistics

        # before executing
        start_time = time.time()

        result = method(*args, **kwargs)

        # after executing
        end_time = time.time()
        statistics.time_stage = end_time - start_time

        return result

    return wrapper


def execute_with_stats(method):

    def wrapper(self, context):
        global statistics

        # before executing
        statistics = Statistics()
        start_time = time.time()

        result = method(self, context)

        # after executing
        files_count_info = '\n{0}ed Files: {1}'.format(
            statistics.context.split(' ')[0],
            statistics.files_count
        )
        info(files_count_info)
        data_blocks_count_info()

        statistics.status = '\nTotal Time'
        statistics.props = None
        end_time(start_time)
        statistics.flush()
        statistics = None

        return result

    return wrapper
