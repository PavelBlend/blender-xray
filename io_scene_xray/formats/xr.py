# addon modules
from .. import rw


def create_cached_file_data(ffname, fparser):
    class State:
        def __init__(self):
            self._cdata = None
            self._cpath = None

        def get_values(self):
            file_path = ffname()
            if self._cpath == file_path:
                return self._cdata
            tmp = None
            if file_path:
                file_data = rw.utils.read_file(file_path)
                tmp = fparser(file_data)
            self._cpath = file_path
            self._cdata = tmp
            return self._cdata

    state = State()
    return lambda self=None: state.get_values()


def parse_shaders(data):
    for (cid, cdata) in rw.read.ChunkedReader(data):
        if cid == 3:
            reader = rw.read.PackedReader(cdata)
            for _ in range(reader.uint32()):
                yield (reader.gets(), '', None)


def parse_gamemtl(data):
    for (cid, data) in rw.read.ChunkedReader(data):
        if cid == 4098:
            for (_, cdata) in rw.read.ChunkedReader(data):
                name, desc = None, None
                for (cccid, ccdata) in rw.read.ChunkedReader(cdata):
                    if cccid == 0x1000:
                        reader = rw.read.PackedReader(ccdata)
                        material_id = reader.getf('<I')[0]
                        name = reader.gets()
                    if cccid == 0x1005:
                        desc = rw.read.PackedReader(ccdata).gets()
                yield (name, desc, material_id)


def parse_shaders_xrlc(data):
    if len(data) % (128 + 16) != 0:
        exit(1)
    reader = rw.read.PackedReader(data)
    for _ in range(len(data) // (128 + 16)):
        name = reader.gets()
        reader.getf('{}s'.format(127 - len(name) + 16))    # skip
        yield (name, '', None)
