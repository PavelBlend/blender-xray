import os
import xray_io
import le


CURRENT_VERSION = 17


class GroupFlags:
    STATE_OPENED = 1 << 0


class GroupChunks:
    VERSION = 0
    OBJECT_LIST = 1
    FLAGS = 3
    REFERENCE = 4
    OPEN_OBJECT_LIST = 5


def dump_reference(data):
    global reader
    reader = xray_io.PackedReader(data)

    reference = read('str', 'reference')
    print('        Reference: "{}"'.format(reference))


def dump_flags(data):
    global reader
    reader = xray_io.PackedReader(data)

    flags = read('I', 'flags')
    flag_state_opened = bool(flags & GroupFlags.STATE_OPENED)
    print('        Flag State Opened:', flag_state_opened)


def dump_version(data):
    global reader
    reader = xray_io.PackedReader(data)

    ver = read('H', 'version')
    print('        Version:', ver)

    if ver != CURRENT_VERSION:
        raise 'unsupported group version'


def dump_group(data):
    chunks = xray_io.ChunkedReader(data).read()

    for chunk_id, chunk_data in chunks:

        if chunk_id == GroupChunks.VERSION:
            print('    VERSION:')
            dump_version(chunk_data)

        elif chunk_id == GroupChunks.OBJECT_LIST:
            print('    OBJECT LIST:')
            le.objects.dump_objects(chunk_data)

        elif chunk_id == GroupChunks.FLAGS:
            print('    OBJECT FLAGS:')
            dump_flags(chunk_data)

        elif chunk_id == GroupChunks.REFERENCE:
            print('    OBJECT REFERENCE:')
            dump_reference(chunk_data)

        # custom object
        elif chunk_id == le.fmt.ObjectChunks.FLAGS:
            print('                    CUSTOM OBJECT FLAGS:')
            le.custom_object.dump_flags(chunk_data)

        elif chunk_id == le.fmt.ObjectChunks.NAME:
            print('                    CUSTOM OBJECT NAME:')
            le.custom_object.dump_name(chunk_data)

        elif chunk_id == le.fmt.ObjectChunks.TRANSFORM:
            print('                    CUSTOM OBJECT TRANSFORM:')
            le.custom_object.dump_transform(chunk_data)

        # unknown chunks
        else:
            print('    unknown chunk', hex(chunk_id), len(chunk_data))


reader = None


def read(fmt, name):
    global reader

    if fmt == 'str':
        value = reader.gets()

    else:
        value = reader.getf('<' + fmt)
        if len(value) == 1:
            value = value[0]

    # print('{} = {}'.format(name, value))

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
