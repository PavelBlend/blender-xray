import xray_io

from . import fmt
from . import general
from . import objects
from . import object_tools
from . import utils


def dump_data(data):
    chunked_reader = xray_io.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader.read():

        # level tag
        if chunk_id == fmt.SceneChunks.LEVEL_TAG:
            print('        LEVEL TAG:')
            general.dump_level_tag(chunk_data)

        # custom objects
        elif chunk_id == fmt.CustomObjectsChunks.OBJECT_COUNT:
            print('        CUSTOM OBJECT COUNT:')
            objects.dump_object_count(chunk_data)

        elif chunk_id == fmt.CustomObjectsChunks.OBJECTS:
            print('        CUSTOM OBJECTS:')
            objects.dump_objects(chunk_data)

        # object tools
        elif chunk_id == fmt.ObjectToolsChunks.VERSION:
            print('        OBJECT TOOLS VERSION:')
            object_tools.dump_version(chunk_data)

        elif chunk_id == fmt.ObjectToolsChunks.FLAGS:
            print('        OBJECT TOOLS FLAGS:')
            object_tools.dump_flags(chunk_data)

        elif chunk_id == fmt.ObjectToolsChunks.APPEND_RANDOM:
            print('        OBJECT TOOLS APPEND RANDOM:')
            object_tools.dump_append_random(chunk_data)

        # unknown chunks
        else:
            raise BaseException('Unsupported chunk: 0x{:x}'.format(chunk_id))


def _dump_part_body(data):
    chunked_reader = xray_io.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader.read():

        if chunk_id == fmt.ToolsChunks.GUID:
            print('    GUID:')
            general.dump_guid(chunk_data)

        elif chunk_id == fmt.ToolsChunks.DATA + fmt.ClassID.OBJECT:
            print('    DATA:')
            dump_data(chunk_data)

        # unknown chunks
        else:
            raise BaseException('Unsupported chunk: 0x{:x}'.format(chunk_id))


def dump_main(path):
    print('\n'*3)

    data = utils.read_file(path)

    print('Dump *.part:', path)
    _dump_part_body(data)

    print('\n'*2)
