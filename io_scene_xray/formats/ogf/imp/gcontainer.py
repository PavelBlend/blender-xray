# addon modules
from .... import rw


def import_fastpath_gcontainer(data, visual, lvl):
    packed_reader = rw.read.PackedReader(data)

    vb_index = packed_reader.getf('<I')[0]
    vb_offset = packed_reader.getf('<I')[0]
    vb_size = packed_reader.getf('<I')[0]
    ib_index = packed_reader.getf('<I')[0]
    ib_offset = packed_reader.getf('<I')[0]
    ib_size = packed_reader.getf('<I')[0]

    vb_slice = slice(vb_offset, vb_offset + vb_size)
    geometry_key = (vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size)
    bpy_mesh = lvl.loaded_fastpath_geometry.get(geometry_key, None)
    if bpy_mesh:
        return bpy_mesh, geometry_key
    vertex_buffers = lvl.fastpath_vertex_buffers
    indices_buffers = lvl.fastpath_indices_buffers
    visual.vertices = vertex_buffers[vb_index].position[vb_slice]

    visual.indices = indices_buffers[ib_index][
        ib_offset : ib_offset + ib_size
    ]
    visual.indices_count = ib_size

    return bpy_mesh, geometry_key


def read_gcontainer_v4(data):
    packed_reader = rw.read.PackedReader(data)

    vb_index = packed_reader.getf('<I')[0]
    vb_offset = packed_reader.getf('<I')[0]
    vb_size = packed_reader.getf('<I')[0]
    ib_index = packed_reader.getf('<I')[0]
    ib_offset = packed_reader.getf('<I')[0]
    ib_size = packed_reader.getf('<I')[0]

    return vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size


def import_vcontainer(visual, lvl, vb_index, vb_offset, vb_size):
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


def import_icontainer(visual, lvl, ib_index, ib_offset, ib_size):
    ib = lvl.indices_buffers[ib_index]
    visual.indices = ib[ib_offset : ib_offset + ib_size]
    visual.indices_count = ib_size


def read_container_v3(data):
    packed_reader = rw.read.PackedReader(data)
    index, offset, size = packed_reader.getf('<3I')
    return index, offset, size
