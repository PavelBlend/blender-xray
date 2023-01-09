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


def import_gcontainer(
        visual, lvl,
        vb_index, vb_offset, vb_size,
        ib_index, ib_offset, ib_size
    ):

    if not (vb_index is None and vb_offset is None and vb_size is None):
        vb_slice = slice(vb_offset, vb_offset + vb_size)
        geometry_key = (vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size)
        bpy_mesh = lvl.loaded_geometry.get(geometry_key, None)
        if bpy_mesh:
            return bpy_mesh, geometry_key
        vertex_buffers = lvl.vertex_buffers
        indices_buffers = lvl.indices_buffers
        visual.vertices = vertex_buffers[vb_index].position[vb_slice]
        visual.normals = vertex_buffers[vb_index].normal[vb_slice]
        visual.uvs = vertex_buffers[vb_index].uv[vb_slice]
        visual.uvs_lmap = vertex_buffers[vb_index].uv_lmap[vb_slice]
        visual.hemi = vertex_buffers[vb_index].color_hemi[vb_slice]
        visual.vb_index = vb_index

        if vertex_buffers[vb_index].color_light:
            visual.light = vertex_buffers[vb_index].color_light[vb_slice]
        if vertex_buffers[vb_index].color_sun:
            visual.sun = vertex_buffers[vb_index].color_sun[vb_slice]
    else:
        bpy_mesh = None
        geometry_key = None

    if not (ib_index is None and ib_offset is None and ib_size is None):
        visual.indices = indices_buffers[ib_index][
            ib_offset : ib_offset + ib_size
        ]
        visual.indices_count = ib_size

    return bpy_mesh, geometry_key


def read_container_v3(data):
    packed_reader = rw.read.PackedReader(data)
    index, offset, size = packed_reader.getf('<3I')
    return index, offset, size
