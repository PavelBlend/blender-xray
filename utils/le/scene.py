import xray_io

from . import fmt
from . import general
from . import objects
from . import object_tools


def dump_data(data):
    chunked_reader = xray_io.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader.read():

        # level tag
        if chunk_id == fmt.SceneChunks.LEVEL_TAG:
            print('        LEVEL TAG:', hex(chunk_id))
            general.dump_level_tag(chunk_data)

        # custom objects
        elif chunk_id == fmt.CustomObjectsChunks.OBJECT_COUNT:
            print('        CUSTOM OBJECT COUNT:', hex(chunk_id))
            objects.dump_object_count(chunk_data)

        elif chunk_id == fmt.CustomObjectsChunks.OBJECTS:
            print('        CUSTOM OBJECTS:', hex(chunk_id))
            objects.dump_objects(chunk_data)

        # object tools
        elif chunk_id == fmt.ObjectToolsChunks.VERSION:
            print('        OBJECT TOOLS VERSION:', hex(chunk_id))
            object_tools.dump_version(chunk_data)

        elif chunk_id == fmt.ObjectToolsChunks.FLAGS:
            print('        OBJECT TOOLS FLAGS:', hex(chunk_id))
            object_tools.dump_flags(chunk_data)

        elif chunk_id == fmt.ObjectToolsChunks.APPEND_RANDOM:
            print('        OBJECT TOOLS APPEND RANDOM:', hex(chunk_id))
            object_tools.dump_append_random(chunk_data)

        # unknown chunks
        else:
            raise BaseException('Unsupported chunk: 0x{:x}'.format(chunk_id))
