import struct


class FastBytes:
    @staticmethod
    def short_at(data, offs):
        return data[offs] | (data[offs + 1] << 8)

    @staticmethod
    def int_at(data, offs):
        return data[offs] | (data[offs + 1] << 8) | (data[offs + 2] << 16) | (data[offs + 3] << 24)

    @staticmethod
    def skip_str_at(data, offs):
        dlen = len(data)
        while (offs < dlen) and (data[offs] != 0):
            offs += 1
        return offs + 1

    @staticmethod
    def str_at(data, offs):
        new_offs = FastBytes.skip_str_at(data, offs)
        return data[offs:new_offs - 1].decode('cp1251'), new_offs


class PackedReader:
    __slots__ = ['__offs', '__data', '__view']
    __PREP_I = struct.Struct('<I')

    def __init__(self, data):
        self.__offs = 0
        self.__data = data
        self.__view = None

    def getb(self, count):
        self.__offs += count
        return self.__data[self.__offs - count:self.__offs]

    def getf(self, fmt):
        size = struct.calcsize(fmt)
        self.__offs += size
        return struct.unpack_from(fmt, self.__data, self.__offs - size)

    def byte(self):
        return self.__data[self._next(1)]

    def int(self):
        return FastBytes.int_at(self.__data, self._next(4))

    def _next(self, size):
        offs = self.__offs
        self.__offs = offs + size
        return offs

    @staticmethod
    def prep(fmt):
        return struct.Struct('<' + fmt)

    def getp(self, prep):
        offs = self.__offs
        self.__offs = offs + prep.size
        return prep.unpack_from(self.__data, offs)

    def gets(self, onerror=None):
        data, offs = self.__data, self.__offs
        new_offs = self.__offs = FastBytes.skip_str_at(data, offs)
        bts = data[offs:new_offs - 1]
        try:
            return str(bts, 'cp1251')
        except UnicodeError as error:
            if onerror is None:
                raise
            onerror(error)
            return str(bts, 'cp1251', errors='replace')

    def getv(self):
        view = self.__view
        if view is None:
            self.__view = view = memoryview(self.__data)
        return view[self.__offs:]

    def skip(self, count):
        self.__offs += count


class ChunkedReader:
    __MASK_COMPRESSED = 0x80000000

    def __init__(self, data):
        self.__offs = 0
        self.__data = data

    def __iter__(self):
        return self

    def __next__(self):
        offs = self.__offs
        data = self.__data
        if offs >= len(data):
            raise StopIteration
        cid, size = struct.unpack_from('II', data, offs)
        if (cid & ChunkedReader.__MASK_COMPRESSED) != 0:
            raise Exception('unsupported: compressed chunk {:#x}'.format(cid))
        offs += 8 + size
        self.__offs = offs
        return cid & ~ChunkedReader.__MASK_COMPRESSED, data[offs - size:offs]

    def next(self, expected_cid):
        cid, data = next(self)
        if cid != expected_cid:
            raise Exception('expected chunk: {}, but found: {}'.format(expected_cid, cid))
        return data

    def nextf(self, expected_cid, fmt):
        return struct.unpack(fmt, self.next(expected_cid))


class PackedWriter():
    def __init__(self):
        self.data = bytearray()

    def putp(self, pkw):
        self.data += pkw.data
        return self

    def putf(self, fmt, *args):
        self.data += struct.pack(fmt, *args)
        return self

    def puts(self, string):
        self.data += string.encode('cp1251')
        self.data += b'\x00'
        return self


class ChunkedWriter():
    def __init__(self):
        self.data = bytearray()

    def put(self, cid, writer):
        self.data += struct.pack('II', cid, len(writer.data))
        self.data += writer.data
        return self
