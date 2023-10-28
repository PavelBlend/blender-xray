# addon modules
from .... import rw


class SlideWindowItem(object):
    def __init__(self, offset, triangles_count, vertices_count):
        self.offset = offset
        self.triangles_count = triangles_count
        self.vertices_count = vertices_count


def import_swi_buffer(packed_reader):
    # old version of the *.ogf format does not contain reserved bytes
    reserved = 0
    items_count = 0
    while not reserved and not packed_reader.is_end():
        reserved = packed_reader.uint32()
        if reserved:
            items_count = reserved

    swis = []

    for index in range(items_count):

        # read swi
        offset = packed_reader.uint32()
        triangles_count, vertices_count = packed_reader.getf('<2H')

        # create swi
        swi = SlideWindowItem(offset, triangles_count, vertices_count)
        swis.append(swi)

    return swis


def import_swi_buffers(data):
    packed_reader = rw.read.PackedReader(data)
    buffers_count = packed_reader.uint32()

    buffers = []
    for index in range(buffers_count):
        buffer = import_swi_buffer(packed_reader)
        buffers.append(buffer)

    return buffers
