import struct


class PackedReader:
    def __init__(self, data):
        self.__offs = 0
        self.__data = data

    def getf(self, fmt):
        s = struct.calcsize(fmt)
        self.__offs += s
        return struct.unpack_from(fmt, self.__data, self.__offs - s)

    def gets(self):
        zpos = self.__data.find(0, self.__offs)
        if zpos == -1:
            zpos = len(self.__data)
        return self.getf('{}sx'.format(zpos - self.__offs))[0].decode('cp1251')


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
        i, s = struct.unpack_from('II', data, offs)
        if (i & ChunkedReader.__MASK_COMPRESSED) != 0:
            raise Exception('unsupported: compressed chunk {:#x}'.format(i))
        offs += 8 + s
        self.__offs = offs
        return i & ~ChunkedReader.__MASK_COMPRESSED, data[offs - s:offs]

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

    def putf(self, fmt, *args):
        self.data += struct.pack(fmt, *args)
        return self

    def puts(self, s):
        self.data += s.encode('cp1251')
        self.data += b'\x00'
        return self


class ChunkedWriter():
    def __init__(self):
        self.data = bytearray()

    def put(self, cid, w):
        self.data += struct.pack('II', cid, len(w.data))
        self.data += w.data
        return self
