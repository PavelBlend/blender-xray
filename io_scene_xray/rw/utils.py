# standart modules
import os

# addon modules
from . import read
from .. import log
from .. import text


def get_chunks(data):
    chunks = {}
    chunked_reader = read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:
        if not chunks.get(chunk_id, None):
            chunks[chunk_id] = chunk_data

    return chunks


def get_reader_chunks(chunked_reader):
    return {chunk_id: chunk_data for chunk_id, chunk_data in chunked_reader}


def read_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            data = file.read()
        return data

    except FileNotFoundError:
        raise log.AppError('No such file!')


def save_file(file_path, writer):
    dir_path = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    name, ext = os.path.splitext(file_name)

    if name.count('.'):
        name = name.replace('.', '_')
        old_path = file_path
        file_path = os.path.join(dir_path, name + ext)
        log.warn(
            text.warn.name_has_dot,
            new=file_path,
            old=old_path
        )

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


def check_file_exists(file_path):
    if not os.path.exists(file_path):
        raise log.AppError(
            text.error.file_not_found,
            log.props(file_path=file_path)
        )


def get_file_data(file_path, update_log=True):
    abs_path = os.path.abspath(file_path)
    if update_log:
        log.update(file=abs_path)
    check_file_exists(abs_path)
    file_data = read_file(abs_path)
    return file_data


def get_file_reader(file_path, chunked=False, update_log=True):
    file_data = get_file_data(file_path, update_log)

    if chunked:
        reader = read.ChunkedReader(memoryview(file_data))
    else:
        reader = read.PackedReader(file_data)

    return reader


def get_file_chunks(file_path):
    file_data = get_file_data(file_path)
    reader = read.ChunkedReader(memoryview(file_data))
    chunks = get_reader_chunks(reader)

    return chunks
