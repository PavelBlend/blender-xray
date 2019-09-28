from .. import xray_io
from . import fmt


class VertexBuffer(object):
    def __init__(self):
        self.position = []
        self.normal = []
        self.color_hemi = []
        self.color_light = []
        self.color_sun = []
        self.uv = []
        self.uv_lmap = []
        self.shader_data = []


def import_vertices_color(packed_reader, vertex_buffer, vertices_count):
    for vertex_index in range(vertices_count):
        # position
        coord_x, coord_y, coord_z = packed_reader.getf('3f')
        vertex_buffer.position.append((coord_x, coord_z, coord_y))
        # normal
        norm_x, norm_y, norm_z, hemi = packed_reader.getf('4B')
        vertex_buffer.normal.append((
            (2.0 * norm_z / 255.0 - 1.0),
            (2.0 * norm_x / 255.0 - 1.0),
            (2.0 * norm_y / 255.0 - 1.0)
        ))
        vertex_buffer.color_hemi.append(hemi / 255)
        # tangent
        tangent = packed_reader.getf('4B')
        # binormal
        binormal = packed_reader.getf('4B')
        # vertex color
        color = packed_reader.getf('4B')
        vertex_buffer.color_light.append((
            color[2] / 255, color[1] / 255, color[0] / 255
        ))
        vertex_buffer.color_sun.append(color[3])
        # texture coordinates
        coord_u, coord_v = packed_reader.getf('2h')
        vertex_buffer.uv.append((
            coord_u / fmt.UV_COEFFICIENT, 1 - coord_v / fmt.UV_COEFFICIENT
        ))


def import_vertices_brush(packed_reader, vertex_buffer, vertices_count):
    for vertex_index in range(vertices_count):
        # position
        coord_x, coord_y, coord_z = packed_reader.getf('3f')
        vertex_buffer.position.append((coord_x, coord_z, coord_y))
        # normal
        norm_x, norm_y, norm_z, hemi = packed_reader.getf('4B')
        vertex_buffer.normal.append((
            (2.0 * norm_z / 255.0 - 1.0),
            (2.0 * norm_x / 255.0 - 1.0),
            (2.0 * norm_y / 255.0 - 1.0)
        ))
        vertex_buffer.color_hemi.append(hemi / 255)
        # tangent
        tangent = packed_reader.getf('4B')
        # binormal
        binormal = packed_reader.getf('4B')
        # texture coordinates
        coord_u, coord_v = packed_reader.getf('2h')
        vertex_buffer.uv.append((
            coord_u / fmt.UV_COEFFICIENT, 1 - coord_v / fmt.UV_COEFFICIENT
        ))
        # light map texture coordinates
        lmap_u, lmap_v = packed_reader.getf('2h')
        vertex_buffer.uv_lmap.append((
            lmap_u / (fmt.LIGHT_MAP_UV_COEFFICIENT),
            1 - lmap_v / (fmt.LIGHT_MAP_UV_COEFFICIENT)
        ))


def import_vertices_tree(packed_reader, vertex_buffer, vertices_count):
    for vertex_index in range(vertices_count):
        # position
        coord_x, coord_y, coord_z = packed_reader.getf('3f')
        vertex_buffer.position.append((coord_x, coord_z, coord_y))
        # normal
        norm_x, norm_y, norm_z, hemi = packed_reader.getf('4B')
        vertex_buffer.normal.append((
            (2.0 * norm_z / 255.0 - 1.0),
            (2.0 * norm_x / 255.0 - 1.0),
            (2.0 * norm_y / 255.0 - 1.0)
        ))
        vertex_buffer.color_hemi.append(hemi / 255)
        # tangent
        tangent = packed_reader.getf('4B')
        # binormal
        binormal = packed_reader.getf('4B')
        # texture coordinates
        coord_u, coord_v = packed_reader.getf('2h')
        vertex_buffer.uv.append((
            coord_u / fmt.UV_COEFFICIENT_2, 1 - coord_v / fmt.UV_COEFFICIENT_2
        ))
        shader_data, unused = packed_reader.getf('2H')
        vertex_buffer.shader_data.append(shader_data)


def import_vertices(packed_reader, vertex_buffer, vertices_count, usage_list):
    if usage_list == fmt.VERTEX_TYPE_TREE:
        import_vertices_tree(packed_reader, vertex_buffer, vertices_count)
    elif usage_list == fmt.VERTEX_TYPE_BRUSH:
        import_vertices_brush(packed_reader, vertex_buffer, vertices_count)
    elif usage_list == fmt.VERTEX_TYPE_COLOR:
        import_vertices_color(packed_reader, vertex_buffer, vertices_count)
    else:
        raise BaseException('Unsupported vertex buffer format')


def import_vertex_buffer_declaration(packed_reader):
    usage_list = []

    while True:
        stream = packed_reader.getf('H')[0]             # ?
        offset = packed_reader.getf('H')[0]             # ?
        type_ = packed_reader.getf('B')[0]              # ?
        method = packed_reader.getf('B')[0]             # ?
        usage = packed_reader.getf('B')[0]              # ?
        usage_index = packed_reader.getf('B')[0]        # ?

        if fmt.types[type_] == fmt.UNUSED:
            break
        else:
            usage_list.append((usage, type_))

    return usage_list


def import_vertex_buffer(packed_reader):
    usage_list = import_vertex_buffer_declaration(packed_reader)
    vertex_buffer = VertexBuffer()
    vertices_count = packed_reader.getf('I')[0]
    import_vertices(packed_reader, vertex_buffer, vertices_count, usage_list)
    return vertex_buffer


def import_vertex_buffers(data):
    packed_reader = xray_io.PackedReader(data)
    vertex_buffers_count = packed_reader.getf('<I')[0]
    vertex_buffers = []

    for vertex_buffer_index in range(vertex_buffers_count):
        vertex_buffer = import_vertex_buffer(packed_reader)
        vertex_buffers.append(vertex_buffer)

    return vertex_buffers
