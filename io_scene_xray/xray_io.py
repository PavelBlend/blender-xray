import struct


class FastBytes:
    @staticmethod
    def short_at(data, offs):
        return data[offs] | (data[offs + 1] << 8)

    @staticmethod
    def int_at(data, offs):
        return data[offs] | (data[offs + 1] << 8) | (data[offs + 2] << 16) | (data[offs + 3] << 24)

    @staticmethod
    def skip_str(data, offs):
        zpos = data.find(0, offs)
        if zpos == -1:
            return len(data)
        return zpos + 1

    @staticmethod
    def str_at(data, offs):
        new_offs = FastBytes.skip_str(data, offs)
        return data[offs:new_offs - 1].decode('cp1251'), new_offs


class PackedReader:
    # __slots__ = ['__offs', '__data']
    __PREP_I = struct.Struct('<I')

    def __init__(self, data):
        self.__offs = 0
        self.__data = data

    def getb(self, count):
        self.__offs += count
        return self.__data[self.__offs - count:self.__offs]

    def getf(self, fmt):
        size = struct.calcsize(fmt)
        self.__offs += size
        return struct.unpack_from(fmt, self.__data, self.__offs - size)

    def byte(self):
        offs = self.__offs
        self.__offs = offs + 1
        return self.__data[offs]

    def int(self):
        return self.getp(PackedReader.__PREP_I)[0]

    @staticmethod
    def prep(fmt):
        return struct.Struct('<' + fmt)

    def getp(self, prep):
        offs = self.__offs
        self.__offs = offs + prep.size
        return prep.unpack_from(self.__data, offs)

    def gets(self, onerror=None):
        # zpos = self.__data.find(0, self.__offs)
        # if zpos == -1:
        #     zpos = len(self.__data)
        data, zpos = self.__data, self.__offs
        dlen = len(data)
        while (zpos != dlen) and (data[zpos] != 0):
            zpos += 1
        bts = self.getf('{}sx'.format(zpos - self.__offs))[0]
        try:
            return bts.decode('cp1251')
        except UnicodeError as error:
            if onerror is None:
                raise
            onerror(error)
            return bts.decode('cp1251', errors='replace')

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
