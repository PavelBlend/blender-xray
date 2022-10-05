# standart modules
import os

# addon modules
from . import read
from .. import log
from .. import text


def get_chunks(data):
    chunked_reader = read.ChunkedReader(data)
    chunks = {}
    for chunk_id, chunk_data in chunked_reader:
        if not chunks.get(chunk_id, None):
            chunks[chunk_id] = chunk_data
    return chunks


def read_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            data = file.read()
        return data
    except FileNotFoundError:
        raise log.AppError('No such file!')


def save_file(file_path, writer):
    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    try:
        with open(file_path, 'wb') as file:
            file.write(writer.data)
    except PermissionError:
        raise log.AppError(
            text.error.file_another_prog,
            log.props(file=os.path.basename(file_path), path=file_path)
        )


def read_text_file(file_path):
    with open(file_path, mode='r', encoding='cp1251') as file:
        data = file.read()
    return data
