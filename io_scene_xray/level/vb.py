from .. import xray_io
from . import fmt


class VertexBuffer(object):
    def __init__(self):
        self.position = []
        self.normal = []
        self.tangent = []
        self.binormal = []
        self.color_hemi = []
        self.color_light = []
        self.color_sun = []
        self.uv = []
        self.uv_fix = []
        self.uv_lmap = []
        self.shader_data = []
        self.vertex_format = None


def get_uv_corrector(value):
    uv_corrector = (value / 255) * (32 / 0x8000)
    return uv_corrector


def import_vertices_fastpath(packed_reader, vertex_buffer, vertices_count):
    for vertex_index in range(vertices_count):
        # position
        coord_x, coord_y, coord_z = packed_reader.getf('<3f')
        vertex_buffer.position.append((coord_x, coord_z, coord_y))


def import_vertices_color_14(packed_reader, vertex_buffer, vertices_count):
    for vertex_index in range(vertices_count):
        # position
        coord_x, coord_y, coord_z = packed_reader.getf('<3f')
        vertex_buffer.position.append((coord_x, coord_z, coord_y))
        # normal
        norm_x, norm_y, norm_z, hemi = packed_reader.getf('<4B')
        vertex_buffer.normal.append((
            (2.0 * norm_z / 255.0 - 1.0),
            (2.0 * norm_x / 255.0 - 1.0),
            (2.0 * norm_y / 255.0 - 1.0)
        ))
        vertex_buffer.color_hemi.append(hemi / 255)
        # tangent
        tangent_x, tangent_y, tangent_z, correct_u = packed_reader.getf('<4B')
        # binormal
        binorm_x, binorm_y, binorm_z, correct_v = packed_reader.getf('<4B')
        # vertex color
        color = packed_reader.getf('<4B')
        vertex_buffer.color_light.append((
            color[2] / 255, color[1] / 255, color[0] / 255
        ))
        vertex_buffer.color_sun.append(color[3])
        # texture coordinates
        coord_u, coord_v = packed_reader.getf('<2h')
        vertex_buffer.uv.append((
            coord_u / fmt.UV_COEFFICIENT  + get_uv_corrector(correct_u),
            1 - coord_v / fmt.UV_COEFFICIENT - get_uv_corrector(correct_v)
        ))


def import_vertices_color_13(packed_reader, vertex_buffer, vertices_count):
    for vertex_index in range(vertices_count):
        # position
        coord_x, coord_y, coord_z = packed_reader.getf('<3f')
        vertex_buffer.position.append((coord_x, coord_z, coord_y))
        # normal
        norm_x, norm_y, norm_z, hemi = packed_reader.getf('<4B')
        vertex_buffer.normal.append((
            (2.0 * norm_z / 255.0 - 1.0),
            (2.0 * norm_x / 255.0 - 1.0),
            (2.0 * norm_y / 255.0 - 1.0)
        ))
        vertex_buffer.color_hemi.append(hemi / 255)
        # tangent
        tangent_x, tangent_y, tangent_z, correct_u = packed_reader.getf('<4B')
        # binormal
        binorm_x, binorm_y, binorm_z, correct_v = packed_reader.getf('<4B')
        # vertex color
        color = packed_reader.getf('<4B')
        vertex_buffer.color_light.append((
            color[2] / 255, color[1] / 255, color[0] / 255
        ))
        vertex_buffer.color_sun.append(color[3])
        # texture coordinates
        coord_u, coord_v = packed_reader.getf('<2f')
        vertex_buffer.uv.append((coord_u, 1 - coord_v))


def import_vertices_brush_14(packed_reader, vertex_buffer, vertices_count):
    for vertex_index in range(vertices_count):
        # position
        coord_x, coord_y, coord_z = packed_reader.getf('<3f')
        vertex_buffer.position.append((coord_x, coord_z, coord_y))
        # normal
        norm_x, norm_y, norm_z, hemi = packed_reader.getf('<4B')
        vertex_buffer.normal.append((
            (2.0 * norm_z / 255.0 - 1.0),
            (2.0 * norm_x / 255.0 - 1.0),
            (2.0 * norm_y / 255.0 - 1.0)
        ))
        vertex_buffer.color_hemi.append(hemi / 255)
        # tangent and corrector of texture u coordinate
        tangent_x, tangent_y, tangent_z, correct_u = packed_reader.getf('<4B')
        # binormal and corrector of texture v coordinate
        binorm_x, binorm_y, binorm_z, correct_v = packed_reader.getf('<4B')
        # texture coordinates
        coord_u, coord_v = packed_reader.getf('<2h')
        vertex_buffer.uv.append((
            coord_u / fmt.UV_COEFFICIENT + get_uv_corrector(correct_u),
            1 - coord_v / fmt.UV_COEFFICIENT - get_uv_corrector(correct_v)
        ))
        # light map texture coordinates
        lmap_u, lmap_v = packed_reader.getf('<2h')
        vertex_buffer.uv_lmap.append((
            lmap_u / fmt.LIGHT_MAP_UV_COEFFICIENT,
            1 - lmap_v / fmt.LIGHT_MAP_UV_COEFFICIENT
        ))


def import_vertices_brush_13(packed_reader, vertex_buffer, vertices_count):
    for vertex_index in range(vertices_count):
        # position
        coord_x, coord_y, coord_z = packed_reader.getf('<3f')
        vertex_buffer.position.append((coord_x, coord_z, coord_y))
        # normal
        norm_x, norm_y, norm_z, hemi = packed_reader.getf('<4B')
        vertex_buffer.normal.append((
            (2.0 * norm_z / 255.0 - 1.0),
            (2.0 * norm_x / 255.0 - 1.0),
            (2.0 * norm_y / 255.0 - 1.0)
        ))
        vertex_buffer.color_hemi.append(hemi / 255)
        # tangent and corrector of texture u coordinate
        tangent_x, tangent_y, tangent_z, correct_u = packed_reader.getf('<4B')
        # binormal and corrector of texture v coordinate
        binorm_x, binorm_y, binorm_z, correct_v = packed_reader.getf('<4B')
        # texture coordinates
        coord_u, coord_v = packed_reader.getf('<2f')
        vertex_buffer.uv.append((coord_u, 1 - coord_v))
        # light map texture coordinates
        lmap_u, lmap_v = packed_reader.getf('<2h')
        vertex_buffer.uv_lmap.append((
            lmap_u / fmt.LIGHT_MAP_UV_COEFFICIENT,
            1 - lmap_v / fmt.LIGHT_MAP_UV_COEFFICIENT
        ))


def import_vertices_tree(packed_reader, vertex_buffer, vertices_count):
    for vertex_index in range(vertices_count):
        # position
        coord_x, coord_y, coord_z = packed_reader.getf('<3f')
        vertex_buffer.position.append((coord_x, coord_z, coord_y))
        # normal
        norm_x, norm_y, norm_z, hemi = packed_reader.getf('<4B')
        vertex_buffer.normal.append((
            (2.0 * norm_z / 255.0 - 1.0),
            (2.0 * norm_x / 255.0 - 1.0),
            (2.0 * norm_y / 255.0 - 1.0)
        ))
        vertex_buffer.color_hemi.append(hemi / 255)
        # tangent and corrector of texture u coordinate
        tangent_x, tangent_y, tangent_z, correct_u = packed_reader.getf('<4B')
        # binormal and corrector of texture v coordinate
        binorm_x, binorm_y, binorm_z, correct_v = packed_reader.getf('<4B')
        # texture coordinates
        coord_u, coord_v = packed_reader.getf('<2h')
        vertex_buffer.uv.append((
            coord_u / fmt.UV_COEFFICIENT_2  + get_uv_corrector(correct_u),
            1 - coord_v / fmt.UV_COEFFICIENT_2 - get_uv_corrector(correct_v)
        ))
        shader_data, unused = packed_reader.getf('<2H')
        vertex_buffer.shader_data.append(shader_data)


def import_vertices(packed_reader, vertex_buffer, vertices_count, usage_list):
    # version 14
    if usage_list == fmt.VERTEX_TYPE_TREE:
        import_vertices_tree(packed_reader, vertex_buffer, vertices_count)
    elif usage_list == fmt.VERTEX_TYPE_BRUSH_14:
        import_vertices_brush_14(packed_reader, vertex_buffer, vertices_count)
    elif usage_list == fmt.VERTEX_TYPE_COLOR_14:
        import_vertices_color_14(packed_reader, vertex_buffer, vertices_count)
    elif usage_list == fmt.VERTEX_TYPE_FASTPATH:
        import_vertices_fastpath(packed_reader, vertex_buffer, vertices_count)
    # version 13
    elif usage_list == fmt.VERTEX_TYPE_BRUSH_13:
        import_vertices_brush_13(packed_reader, vertex_buffer, vertices_count)
    elif usage_list == fmt.VERTEX_TYPE_COLOR_13:
        import_vertices_color_13(packed_reader, vertex_buffer, vertices_count)
    else:
        raise BaseException('Unsupported vertex buffer format', usage_list)


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
