# addon modules
from .. import fmt
from .... import rw


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
        self.float_normals = False


def get_uv_corrector(value):
    uv_corrector = (value / 255) * (32 / 0x8000)
    return uv_corrector


def import_vertices(
        xrlc_version,
        packed_reader,
        vertex_buffer,
        vertices_count,
        usage_list
    ):
    code = ''
    code += 'for vertex_index in range({}):\n'.format(vertices_count)
    has_uv_corrector = False
    for usage_info in usage_list:
        data_type = usage_info[2]
        usage = usage_info[4]
        usage_index = usage_info[5]
        data_format = fmt.types_struct[data_type]
        data_type = fmt.types[data_type]
        usage = fmt.usage[usage]
        if usage == fmt.POSITION:
            code += '    coord_x, coord_y, coord_z = packed_reader.getf("<{}")\n'.format(data_format)
            code += '    vertex_buffer.position.append((coord_x, coord_z, coord_y))\n'
        elif usage == fmt.NORMAL:
            code += '    norm_x, norm_y, norm_z, hemi = packed_reader.getf("<{}")\n'.format(data_format)
            code += '    vertex_buffer.normal.append((\n' \
                    '       norm_z,\n' \
                    '       norm_x,\n' \
                    '       norm_y\n' \
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


def import_vertices_d3d7(
        level,
        packed_reader,
        vertex_buffer,
        vertices_count,
        vertex_format
    ):
    code = ''
    code += 'for vertex_index in range({0}):\n'.format(vertices_count)
    # xyz, normal, diffuse, tex coord

    if (vertex_format & fmt.D3D7FVF.POSITION_MASK) == fmt.D3D7FVF.XYZ:
        code += '    coord_x, coord_y, coord_z = packed_reader.getf("<3f")\n'
        code += '    vertex_buffer.position.append((coord_x, coord_z, coord_y))\n'

    if vertex_format & fmt.D3D7FVF.NORMAL:
        vertex_buffer.float_normals = True
        code += '    norm_x, norm_y, norm_z = packed_reader.getf("<3f")\n'
        code += '    vertex_buffer.normal.append((norm_z, norm_x, norm_y))\n'

    if vertex_format & fmt.D3D7FVF.DIFFUSE:
        code += '    red, green, blue, unknown = packed_reader.getf("<4B")\n'
        code += '    red = red / 255\n'
        code += '    green = green / 255\n'
        code += '    blue = blue / 255\n'
        code += '    vertex_buffer.color_light.append((red, green, blue))\n'

    tex_coord = (vertex_format & fmt.D3D7FVF.TEXCOUNT_MASK) >> fmt.D3D7FVF.TEXCOUNT_SHIFT

    lmap_uv_code = ''
    if tex_coord in (1, 2):
        tex_uv_code = '    coord_u, coord_v = packed_reader.getf("<2f")\n'
        tex_uv_code += '    vertex_buffer.uv.append((coord_u, 1 - coord_v))\n'
    if tex_coord == 2:
        lmap_uv_code = '    lmap_u, lmap_v = packed_reader.getf("<2f")\n'
        lmap_uv_code += '    vertex_buffer.uv_lmap.append((lmap_u, lmap_v))\n'
    if level.xrlc_version >= fmt.VERSION_5:
        code += tex_uv_code
        code += lmap_uv_code
    else:
        code += lmap_uv_code
        code += tex_uv_code

    exec(code)


def import_vertex_buffer_declaration(packed_reader):
    usage_list = []

    while True:
        stream = packed_reader.getf('<H')[0]             # ?
        offset = packed_reader.getf('<H')[0]
        type_ = packed_reader.getf('<B')[0]
        method = packed_reader.getf('<B')[0]             # ?
        usage = packed_reader.getf('<B')[0]
        usage_index = packed_reader.getf('<B')[0]

        if fmt.types[type_] == fmt.UNUSED:
            break
        else:
            usage_list.append((
                stream,
                offset,
                type_,
                method,
                usage,
                usage_index
            ))

    return usage_list


def import_vertex_buffer(packed_reader, level):
    if level.xrlc_version >= fmt.VERSION_9:
        usage_list = import_vertex_buffer_declaration(packed_reader)
        vertex_buffer = VertexBuffer()
        vertices_count = packed_reader.uint32()
        import_vertices(
            level.xrlc_version,
            packed_reader,
            vertex_buffer,
            vertices_count,
            usage_list
        )
    return vertex_buffer


def import_vertex_buffer_d3d7(packed_reader, level):
    if level.xrlc_version <= fmt.VERSION_9:
        vertex_format = packed_reader.uint32()
        vertices_count = packed_reader.uint32()
        vertex_buffer = VertexBuffer()
        import_vertices_d3d7(
            level,
            packed_reader,
            vertex_buffer,
            vertices_count,
            vertex_format
        )
    return vertex_buffer


def _get_vbs_data(level, chunks, chunks_ids):
    vbs_data = chunks.pop(chunks_ids.VB, None)
    import_fun = import_vertex_buffer

    if level.xrlc_version <= fmt.VERSION_8:
        import_fun = import_vertex_buffer_d3d7

    elif level.xrlc_version == fmt.VERSION_9:
        if not vbs_data:
            vbs_data = chunks.pop(chunks_ids.VB_OLD)
            import_fun = import_vertex_buffer_d3d7

    return vbs_data, import_fun


def import_vertex_buffers(level, chunks, chunks_ids):
    data, import_fun = _get_vbs_data(level, chunks, chunks_ids)
    vbs_reader = rw.read.PackedReader(data)
    buffers_count = vbs_reader.uint32()

    vertex_buffers = []
    for buffer_index in range(buffers_count):
        vertex_buffer = import_fun(vbs_reader, level)
        vertex_buffers.append(vertex_buffer)

    level.vertex_buffers = vertex_buffers
