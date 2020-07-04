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


def import_vertices(
        xrlc_version, packed_reader, vertex_buffer, vertices_count, usage_list
    ):
    code = ''
    code += 'for vertex_index in range({}):\n'.format(vertices_count)
    has_uv_corrector = False
    for usage, data_type, usage_index in usage_list:
        data_format = fmt.types_struct[data_type]
        data_type = fmt.types[data_type]
        usage = fmt.usage[usage]
        if usage == fmt.POSITION:
            code += '    coord_x, coord_y, coord_z = packed_reader.getf("<{}")\n'.format(data_format)
            code += '    vertex_buffer.position.append((coord_x, coord_z, coord_y))\n'
        elif usage == fmt.NORMAL:
            code += '    norm_x, norm_y, norm_z, hemi = packed_reader.getf("<{}")\n'.format(data_format)
            code += '    vertex_buffer.normal.append((\n' \
                    '       norm_x,\n' \
                    '       norm_y,\n' \
                    '       norm_z\n' \
                    '    ))\n'
            code += '    vertex_buffer.color_hemi.append(hemi / 255)\n'
        elif usage == fmt.TANGENT:
            code += '    tangent_x, tangent_y, tangent_z, correct_u = packed_reader.getf("<{}")\n'.format(data_format)
            has_uv_corrector = True
        elif usage == fmt.BINORMAL:
            code += '    binorm_x, binorm_y, binorm_z, correct_v = packed_reader.getf("<{}")\n'.format(data_format)
            has_uv_corrector = True
        elif usage == fmt.TEXCOORD:
            if usage_index == 0:    # texture uv
                if data_type in (fmt.FLOAT2, fmt.SHORT2):
                    code += '    coord_u, coord_v = packed_reader.getf("<{}")\n'.format(data_format)
                elif data_type == fmt.SHORT4:
                    if xrlc_version >= fmt.VERSION_12:
                        code += '    coord_u, coord_v, shader_data, unused = packed_reader.getf("<{}")\n'.format(data_format)
                    else:
                        code += '    coord_u, coord_v, lmap_u, lmap_v = packed_reader.getf("<{}")\n'.format(data_format)
                if data_type == fmt.FLOAT2:
                    code += '    vertex_buffer.uv.append((coord_u, 1 - coord_v))\n'
                elif data_type == fmt.SHORT2:
                    if has_uv_corrector:
                        code += '    vertex_buffer.uv.append((\n' \
                                '        coord_u / fmt.UV_COEFFICIENT + get_uv_corrector(correct_u),\n' \
                                '        1 - coord_v / fmt.UV_COEFFICIENT - get_uv_corrector(correct_v)\n' \
                                '    ))\n'
                    else:
                        code += '    vertex_buffer.uv.append((\n' \
                                '        coord_u / fmt.UV_COEFFICIENT,\n' \
                                '        1 - coord_v / fmt.UV_COEFFICIENT\n' \
                                '    ))\n'
                elif data_type == fmt.SHORT4:
                    if xrlc_version >= fmt.VERSION_12:
                        if has_uv_corrector:
                            code += '    vertex_buffer.uv.append((\n' \
                                    '        coord_u / fmt.UV_COEFFICIENT_2 + get_uv_corrector(correct_u),\n' \
                                    '        1 - coord_v / fmt.UV_COEFFICIENT_2 - get_uv_corrector(correct_v)\n' \
                                    '    ))\n'
                        else:
                            code += '    vertex_buffer.uv.append((\n' \
                                    '        coord_u / fmt.UV_COEFFICIENT_2,\n' \
                                    '        1 - coord_v / fmt.UV_COEFFICIENT_2\n' \
                                    '    ))\n'
                        code += '    vertex_buffer.shader_data.append(shader_data)\n'
                    else:
                        code += '    vertex_buffer.uv.append((\n' \
                                '        coord_u / fmt.UV_COEFFICIENT,\n' \
                                '        1 - coord_v / fmt.UV_COEFFICIENT\n' \
                                '    ))\n' \
                                '    vertex_buffer.uv_lmap.append((\n' \
                                '        lmap_u / fmt.LIGHT_MAP_UV_COEFFICIENT,\n' \
                                '        1 - lmap_v / fmt.LIGHT_MAP_UV_COEFFICIENT\n' \
                                '    ))\n'
            elif usage_index == 1:    # lmap uv
                code += '    lmap_u, lmap_v = packed_reader.getf("<{}")\n'.format(data_format)
                if data_type == fmt.SHORT2:
                    code += '    lmap_u = lmap_u / fmt.LIGHT_MAP_UV_COEFFICIENT\n'
                    code += '    lmap_v = 1 - lmap_v / fmt.LIGHT_MAP_UV_COEFFICIENT\n'
                code += '    vertex_buffer.uv_lmap.append((lmap_u, lmap_v))\n'
            else:
                raise BaseException('Unsupported uv usage index: {}'.format(usage_index))
        elif usage == fmt.COLOR:
            code += '    blue, green, red, sun = packed_reader.getf("<{}")\n'.format(data_format)
            if data_type == fmt.D3DCOLOR:
                code += '    red = red / 255\n'
                code += '    green = green / 255\n'
                code += '    blue = blue / 255\n'
            code += '    vertex_buffer.color_light.append((\n' \
                    '       red, green, blue\n' \
                    '    ))\n'
            code += '    vertex_buffer.color_sun.append(sun)\n'
    exec(code)


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
            usage_list.append((usage, type_, usage_index))

    return usage_list


def import_vertex_buffer(packed_reader, xrlc_version):
    if xrlc_version >= fmt.VERSION_10:
        usage_list = import_vertex_buffer_declaration(packed_reader)
        vertex_buffer = VertexBuffer()
        vertices_count = packed_reader.getf('I')[0]
        import_vertices(
            xrlc_version, packed_reader, vertex_buffer,
            vertices_count, usage_list
        )
    return vertex_buffer


def import_vertex_buffers(data, xrlc_version):
    packed_reader = xray_io.PackedReader(data)
    vertex_buffers_count = packed_reader.getf('<I')[0]
    vertex_buffers = []

    for vertex_buffer_index in range(vertex_buffers_count):
        vertex_buffer = import_vertex_buffer(packed_reader, xrlc_version)
        vertex_buffers.append(vertex_buffer)

    return vertex_buffers
