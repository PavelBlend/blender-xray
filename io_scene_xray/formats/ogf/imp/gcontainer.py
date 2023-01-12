# addon modules
from .... import rw


def load_vcontainer(visual, lvl, vb_index, vb_offset, vb_size):
    vb = lvl.vertex_buffers[vb_index]
    vb_slice = slice(vb_offset, vb_offset + vb_size)

    visual.vertices = vb.position[vb_slice]
    visual.normals = vb.normal[vb_slice]
    visual.uvs = vb.uv[vb_slice]
    visual.uvs_lmap = vb.uv_lmap[vb_slice]
    visual.hemi = vb.color_hemi[vb_slice]
    visual.vb_index = vb_index

    if vb.color_light:
        visual.light = vb.color_light[vb_slice]

    if vb.color_sun:
        visual.sun = vb.color_sun[vb_slice]


def load_icontainer(visual, lvl, ib_index, ib_offset, ib_size):
    ib = lvl.indices_buffers[ib_index]
    visual.indices = ib[ib_offset : ib_offset + ib_size]
    visual.indices_count = ib_size


def read_container(packed_reader):
    index, offset, size = packed_reader.getf('<3I')
    return index, offset, size


def read_container_v3(data):
    packed_reader = rw.read.PackedReader(data)
    return read_container(packed_reader)


def read_gcontainer_v4(data):
    packed_reader = rw.read.PackedReader(data)

    vb_index, vb_offset, vb_size = read_container(packed_reader)
    ib_index, ib_offset, ib_size = read_container(packed_reader)

    return vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size
