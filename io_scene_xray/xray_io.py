# standart modules
import struct

# blender modules
import numpy

# addon modules
from . import lzhuf


ENCODE_ERROR = BaseException


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
    def skip_str_at_a(data, offs):
        dlen = len(data)
        while (offs < dlen) and (data[offs] != 0xa):
            offs += 1
        return offs + 1

    @staticmethod
    def str_at(data, offs):
        new_offs = FastBytes.skip_str_at(data, offs)
        return data[offs:new_offs - 1].decode('cp1251'), new_offs


class PackedReader:
    __slots__ = ['__offs', '__data', '__view']
    __PREP_I = struct.Struct('<I')
    __S_FFF = struct.Struct('<3f')
    __NUMPY_FORMATS = {'f': numpy.float32, }

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

    def getv3f(self):
        # get vertex coord
        coord_x, coord_y, coord_z = struct.unpack_from(
            '<3f',
            self.__data,
            self.__offs
        )
        self.__offs += 12
        return coord_x, coord_z, coord_y

    def getv3fp(self):
        # get vector 3-float using prep
        vec = self.getp(self.__S_FFF)
        return vec[0], vec[2], vec[1]

    def getn3f(self):
        # get vertex normal
        coord_x, coord_y, coord_z = struct.unpack_from(
            '<3f',
            self.__data,
            self.__offs
        )
        self.__offs += 12
        return coord_z, coord_y, coord_x

    def get_array(self, fmt, count):
        dtype_format = self.__NUMPY_FORMATS.get(fmt, None)
        if not dtype_format:
            raise Exception('Unsupported numpy format: {}'.format(fmt))
        dtype = numpy.dtype(dtype_format)
        dtype = dtype.newbyteorder('<')
        size = dtype.itemsize
        verts = numpy.frombuffer(
            self.__data,
            dtype=dtype,
            count=count,
            offset=self.__offs
        )
        self.__offs += size * count
        return verts

    def byte(self):
        return self.__data[self._next(1)]

    def int(self):
        return FastBytes.int_at(self.__data, self._next(4))

    def getq16f(self, min_val, max_val):
        # get quantized 16 bit float value
        u16_val = struct.unpack_from('<H', self.__data, self.__offs)[0]
        self.__offs += 2
        return (u16_val * (max_val - min_val)) / 0xffff + min_val

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
                raise error
            onerror(error)
            return str(bts, 'cp1251', errors='replace')

    def gets_a(self, onerror=None):
        data, offs = self.__data, self.__offs
        new_offs = self.__offs = FastBytes.skip_str_at_a(data, offs)
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

    def offset(self):
        return self.__offs

    def set_offset(self, offset):
        self.__offs = offset

    def is_end(self):
        return self.__offs >= len(self.__data)


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
        cid = FastBytes.int_at(data, offs)
        size = FastBytes.int_at(data, offs + 4)
        offs += 8
        self.__offs = offs + size
        if cid & ChunkedReader.__MASK_COMPRESSED:
            cid &= ~ChunkedReader.__MASK_COMPRESSED
            textsize = FastBytes.int_at(data, offs)
            buffer = data[offs + 4:offs + size]
            return cid, memoryview(lzhuf.decompress_buffer(buffer, textsize))
        return cid, data[offs:offs + size]

    def next(self, expected_cid, no_error=False):
        cid, data = next(self)
        if cid != expected_cid:
            if no_error:
                return
            else:
                raise Exception('expected chunk: {}, but found: {}'.format(
                    expected_cid,
                    cid
                ))
        return data

    def nextf(self, expected_cid, fmt):
        return struct.unpack(fmt, self.next(expected_cid))

    def get_size(self):
        return len(self.__data)


class PackedWriter():
    def __init__(self):
        self.data = bytearray()

    def putp(self, pkw):
        self.data += pkw.data

    def putf(self, fmt, *args):
        self.data += struct.pack(fmt, *args)

    def putv3f(self, vec):
        # write vertex coord
        self.data += struct.pack('<3f', vec[0], vec[2], vec[1])

    def puts(self, string):
        try:
            self.data += string.encode('cp1251')
        except UnicodeEncodeError:
            raise ENCODE_ERROR('Not valid string: {}'.format(string))
        self.data += b'\x00'

    def replace(self, offset, byte_list):
        for byte_index, byte in enumerate(byte_list):
            self.data[offset + byte_index] = byte


class ChunkedWriter():
    def __init__(self):
        self.data = bytearray()

    def put(self, cid, writer):
        self.data += struct.pack('II', cid, len(writer.data))
        self.data += writer.data
