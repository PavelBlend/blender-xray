import xray_io

from . import fmt
from . import scene
from . import general
from . import utils


def _dump_part_body(data):
    chunked_reader = xray_io.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader.read():

        if chunk_id == fmt.ToolsChunks.GUID:
            print('    GUID:')
            general.dump_guid(chunk_data)

        elif chunk_id == fmt.ToolsChunks.DATA + fmt.ClassID.OBJECT:
            print('    DATA:')
            scene.dump_data(chunk_data)

        # unknown chunks
        else:
            raise BaseException('Unsupported chunk: 0x{:x}'.format(chunk_id))


def dump_main(path):
    print('\n'*3)

    data = utils.read_file(path)

    print('Dump *.part:', path)
    _dump_part_body(data)

    print('\n'*2)
