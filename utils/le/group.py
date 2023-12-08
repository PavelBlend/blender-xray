import xray_io
from . import fmt
from . import objects
from . import custom_object


def _dump_reference(data):
    packed_reader = xray_io.PackedReader(data)

    reference = packed_reader.gets()

    print('        Reference: "{}"'.format(reference))


def _dump_flags(data):
    packed_reader = xray_io.PackedReader(data)

    flags = packed_reader.getf('<I')[0]

    print('        Flag State Opened:', bool(flags&fmt.GroupFlags.STATE_OPENED))


def _dump_version(data):
    packed_reader = xray_io.PackedReader(data)

    ver = packed_reader.getf('<H')[0]

    if ver != fmt.GROUP_VERSION:
        raise BaseException('Unsupported group version: {}'.format(ver))

    print('        Version:', ver)


def dump_group(data):
    chunks = xray_io.ChunkedReader(data).read()

    for chunk_id, chunk_data in chunks:

        # group object
        if chunk_id == fmt.GroupChunks.VERSION:
            print('    VERSION:')
            _dump_version(chunk_data)

        elif chunk_id == fmt.GroupChunks.OBJECT_LIST:
            print('    OBJECT LIST:')
            objects.dump_objects(chunk_data)

        elif chunk_id == fmt.GroupChunks.FLAGS:
            print('    OBJECT FLAGS:')
            _dump_flags(chunk_data)

        elif chunk_id == fmt.GroupChunks.REFERENCE:
            print('    OBJECT REFERENCE:')
            _dump_reference(chunk_data)

        # custom object
        elif chunk_id == fmt.ObjectChunks.FLAGS:
            print('                    CUSTOM OBJECT FLAGS:')
            custom_object.dump_flags(chunk_data)

        elif chunk_id == fmt.ObjectChunks.NAME:
            print('                    CUSTOM OBJECT NAME:')
            custom_object.dump_name(chunk_data)

        elif chunk_id == fmt.ObjectChunks.TRANSFORM:
            print('                    CUSTOM OBJECT TRANSFORM:')
            custom_object.dump_transform(chunk_data)

        # unknown chunks
        else:
            raise BaseException('Unsupported chunk: 0x{:x}'.format(chunk_id))
