import struct


class PackedReader:
    def __init__(self, data):
        self.__offs = 0
        self.__data = data

    def getf(self, fmt):
        s = struct.calcsize(fmt)
        self.__offs += s
        return struct.unpack_from(fmt, self.__data, self.__offs - s)


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

    def nextf(self, expected_cid, fmt):
        cid, data = next(self)
        if cid != expected_cid:
            raise Exception('expected chunk: {}, but found: {}'.format(expected_cid, cid))
        return struct.unpack(fmt, data)
