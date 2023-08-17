import os
import xray_io


CURRENT_VERSION = 17


class GroupFlags:
    STATE_OPENED = 1 << 0


class GroupChunks:
    VERSION = 0
    OBJECT_LIST = 1
    FLAGS = 3
    REFERENCE = 4
    OPEN_OBJECT_LIST = 5


class CustomObjectChunks:
    PARAMS = 0xf900
    LOCK = 0xf902
    TRANSFORM = 0xf903
    GROUP = 0xf904
    MOTION = 0xf905
    FLAGS = 0xf906
    NAME = 0xf907
    MOTION_PARAM = 0xf908


class SceneChunks:
    OBJECT_CLASS = 0x7703
    LEVEL_TAG = 0x7777


def dump_reference(data):
    global reader
    reader = xray_io.PackedReader(data)

    reference = read('str', 'reference')


def dump_flags(data):
    global reader
    reader = xray_io.PackedReader(data)

    flags = read('I', 'flags')
    flag_state_opened = bool(flags & GroupFlags.STATE_OPENED)
    print('flag_state_opened =', flag_state_opened)


def dump_level_tag(data):
    chunks = xray_io.ChunkedReader(data).read()

    for chunk_id, chunk_data in chunks:
        print('unknown custom object chunk', hex(chunk_id), len(chunk_data))


def dump_object_class(data):
    global reader
    reader = xray_io.PackedReader(data)

    read('I', 'object_class')


def dump_object(data):
    chunks = xray_io.ChunkedReader(data).read()

    for chunk_id, chunk_data in chunks:

        if chunk_id == SceneChunks.OBJECT_CLASS:
            dump_object_class(chunk_data)

        elif chunk_id == SceneChunks.LEVEL_TAG:
            dump_level_tag(chunk_data)

        else:
            print('unknown object chunk', hex(chunk_id), len(chunk_data))


def dump_object_list(data):
    chunks = xray_io.ChunkedReader(data).read()

    for chunk_id, chunk_data in chunks:
        print('\n\tobject', chunk_id)
        dump_object(chunk_data)

    print()


def dump_version(data):
    global reader
    reader = xray_io.PackedReader(data)

    ver = read('H', 'version')

    if ver != CURRENT_VERSION:
        raise 'unsupported group version'


def dump_group(data):
    chunks = xray_io.ChunkedReader(data).read()

    for chunk_id, chunk_data in chunks:

        if chunk_id == GroupChunks.VERSION:
            dump_version(chunk_data)

        elif chunk_id == GroupChunks.OBJECT_LIST:
            dump_object_list(chunk_data)

        elif chunk_id == GroupChunks.FLAGS:
            dump_flags(chunk_data)

        elif chunk_id == GroupChunks.REFERENCE:
            dump_reference(chunk_data)

        else:
            print('unknown chunk', hex(chunk_id), len(chunk_data))


reader = None


def read(fmt, name):
    global reader

    if fmt == 'str':
        value = reader.gets()

    else:
        value = reader.getf('<' + fmt)
        if len(value) == 1:
            value = value[0]

    print('{} = {}'.format(name, value))

    return value


# search *.group files

group_files = []

for root, dirs, files in os.walk(os.curdir):

    for file in files:
        ext = os.path.splitext(file)[-1]

        if ext == '.group':
            path = os.path.join(root, file)
            path = os.path.abspath(path)
            group_files.append(path)

# dump files

for path in reversed(group_files):

    with open(path, 'rb') as file:
        data = file.read()

    print('dump file: "{}"'.format(path))
    dump_group(data)
