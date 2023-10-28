# standart modules
import os


def get_level_dir(file_path):
    return os.path.dirname(file_path)


def get_level_name(file_path):
    dir_path = get_level_dir(file_path)
    return os.path.basename(dir_path)
