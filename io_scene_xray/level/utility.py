# standart modules
import os

# addon modules
from .. import utils
from .. import xray_io


def get_level_dir(file_path):
    dir_path = os.path.dirname(file_path)
    return dir_path


def get_level_name(file_path):
    dir_path = get_level_dir(file_path)
    level_name = os.path.basename(dir_path)
    return level_name


def get_level_reader(file_path):
    data = utils.read_file(file_path)
    chunked_reader = xray_io.ChunkedReader(data)
    return chunked_reader
