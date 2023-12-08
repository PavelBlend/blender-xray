import xray_io

from . import fmt
from . import part
from . import utils


def _dump_version(data):
    packed_reader = xray_io.PackedReader(data)

    version = packed_reader.getf('<I')[0]

    if version != fmt.SCENE_VERSION:
        raise BaseException('unsupported scene format: {}'.format(version))

    print('        Version:', version)


def _dump_scene_body(data):
    chunked_reader = xray_io.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader.read():

        if chunk_id == fmt.SceneChunks.VERSION:
            print('    VERSION:')
            _dump_version(chunk_data)

        elif chunk_id == fmt.ToolsChunks.DATA + fmt.ClassID.OBJECT:
            print('    DATA:')
            part.dump_data(chunk_data)

        # unknown chunks
        else:
            raise BaseException('Unsupported chunk: 0x{:x}'.format(chunk_id))


def dump_main(path):
    print('\n'*3)

    data = utils.read_file(path)

    print('Dump *.level:', path)
    _dump_scene_body(data)

    print('\n'*2)
