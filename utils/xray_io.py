import struct


class PackedReader:
    str_end = 0
    FILE = None

    def __init__(self, data):
        self.offs = 0
        self.data = data

    def getf(self, fmt):
        size = struct.calcsize(fmt)
        value = struct.unpack_from(fmt, self.data, self.offs)
        self.offs += size
        return value

    def gets(self):
        zero_pos = self.offs
        end = len(self.data)
        while (zero_pos + 1 < end) and (self.data[zero_pos] != self.str_end):
            zero_pos += 1
        string = self.getf('{}sx'.format(zero_pos - self.offs))[0]
        try:
            return string.decode('cp1251')
        except UnicodeError as error:
            return string.decode('cp1251', errors='replace')

    def readed(self):
        size = len(self.data)
        if self.offs != size:
            print('{} unreaded bytes: {}\n'.format(self.FILE, size - self.offs))
            raise 'error'

    def is_end(self):
        return self.offs >= len(self.data)


class ChunkedReader:
    __MASK_COMPRESSED = 0x80000000

    def __init__(self, data):
        self.offs = 0
        self.data = data

    def read(self):
        chunks = []
        while self.offs < len(self.data):
            chunk_id, chunk_size = struct.unpack_from('<2I', self.data, self.offs)
            if chunk_id == 0x0 and not chunk_size:    # bad file (build 1472)
                return chunks
            self.offs += 8
            chunk_data = self.data[self.offs : self.offs + chunk_size]
            self.offs += chunk_size
            if (chunk_id & ChunkedReader.__MASK_COMPRESSED) != 0:
                print('unsupported: compressed chunk {:#x}'.format(i))
                continue
            chunk_id = chunk_id & ~ChunkedReader.__MASK_COMPRESSED
            chunks.append((chunk_id, chunk_data))
        return chunks
