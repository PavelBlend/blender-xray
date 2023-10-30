# addon modules
from .. import fmt
from .... import rw


class VertexBuffer:
    def __init__(self):
        # geometry
        self.position = []
        self.normal = []

        # texture coordinates
        self.uv = []
        self.uv_lmap = []

        # vertex colors
        self.color_hemi = []
        self.color_light = []
        self.color_sun = []

        self.float_normals = False


class Code:
    def __init__(self):
        self.tabs = 0
        self.lines = []

    def add_indent(self):
        ''' Add 4 spaces indentation level. '''
        self.tabs += 1

    def add_line(self, line):
        ''' Add a line of code to the end. '''
        self.lines.append(' ' * self.tabs * 4 + line)

    def get_code(self):
        ''' Get full code. '''
        code = self._get_merged_lines()
        return code

    def _get_merged_lines(self):
        return '\n'.join(self.lines)


UV_CORRECTOR = '({} / 255) * (32 / 0x8000)'
CORRECTOR_U = UV_CORRECTOR.format('correct_u')
CORRECTOR_V = UV_CORRECTOR.format('correct_v')


def _get_tex_uv_code(code, ver, data_type, reader_code, has_corr):
    if data_type == fmt.FLOAT2:
        code.add_line('coord_u, coord_v' + reader_code)
        code.add_line('vb.uv.append((coord_u, 1 - coord_v))')

    elif data_type == fmt.SHORT2:
        code.add_line('coord_u, coord_v' + reader_code)

        if has_corr:
            code.add_line(
                'vb.uv.append(('
                    'coord_u / fmt.UV_COEFFICIENT + {0}, '
                    '1 - coord_v / fmt.UV_COEFFICIENT - {1}'
                '))'.format(
                    CORRECTOR_U,
                    CORRECTOR_V
                )
            )
        else:
            code.add_line(
                'vb.uv.append(('
                    'coord_u / fmt.UV_COEFFICIENT, '
                    '1 - coord_v / fmt.UV_COEFFICIENT'
                '))'
            )

    elif data_type == fmt.SHORT4:

        if ver >= fmt.VERSION_12:
            # MU meshes
            code.add_line(
                'coord_u, coord_v, wind_coef, _' + reader_code
            )

            if has_corr:
                code.add_line(
                    'vb.uv.append(('
                        'coord_u / fmt.UV_COEFFICIENT_2 + {0}, '
                        '1 - coord_v / fmt.UV_COEFFICIENT_2 - {1}'
                    '))'.format(
                        CORRECTOR_U,
                        CORRECTOR_V
                    )
                )
            else:
                code.add_line(
                    'vb.uv.append(('
                        'coord_u / fmt.UV_COEFFICIENT_2, '
                        '1 - coord_v / fmt.UV_COEFFICIENT_2'
                    '))'
                )

        else:
            code.add_line('coord_u, coord_v, lmap_u, lmap_v' + reader_code)
            code.add_line(
                'vb.uv.append(('
                    'coord_u / fmt.UV_COEFFICIENT, '
                    '1 - coord_v / fmt.UV_COEFFICIENT'
                '))'
            )
            code.add_line(
                'vb.uv_lmap.append(('
                    'lmap_u / fmt.LIGHT_MAP_UV_COEFFICIENT, '
                    '1 - lmap_v / fmt.LIGHT_MAP_UV_COEFFICIENT'
                '))'
            )


def _get_uv_code(code, ver, data_type, usage_index, reader_code, has_corr):
    # texture uv
    if usage_index == 0:
        _get_tex_uv_code(code, ver, data_type, reader_code, has_corr)

    # lmap uv
    elif usage_index == 1:
        code.add_line('lmap_u, lmap_v' + reader_code)

        if data_type == fmt.SHORT2:
            code.add_line('lmap_u /= fmt.LIGHT_MAP_UV_COEFFICIENT')
            code.add_line('lmap_v /= fmt.LIGHT_MAP_UV_COEFFICIENT')

        code.add_line('vb.uv_lmap.append((lmap_u, 1 - lmap_v))')

    else:
        raise ValueError(
            'Unsupported UV usage index: {}'.format(usage_index)
        )


def _import_vertices_d3d9(ver, reader, vb, verts_count, usage_list):
    code = Code()

    code.add_line('for _ in range({}):'.format(verts_count))
    code.add_indent()

    # has uv corrector
    has_corr = False

    for usage_info in usage_list:

        data_type = usage_info[2]
        usage = usage_info[4]
        usage_index = usage_info[5]
        data_format = fmt.types_struct[data_type]
        data_type = fmt.types[data_type]
        usage = fmt.usage[usage]

        reader_code = ' = reader.getf("<{}")'.format(data_format)

        # position
        if usage == fmt.POSITION:
            code.add_line('pos_x, pos_y, pos_z' + reader_code)
            code.add_line('vb.position.append((pos_x, pos_z, pos_y))')

        # normal
        elif usage == fmt.NORMAL:
            code.add_line('norm_x, norm_y, norm_z, hemi' + reader_code)
            code.add_line('vb.normal.append((norm_z, norm_x, norm_y))')
            code.add_line('vb.color_hemi.append(hemi / 255)')

        # tangent
        elif usage == fmt.TANGENT:
            has_corr = True
            code.add_line('tan_x, tan_y, tan_z, correct_u' + reader_code)

        # binormal
        elif usage == fmt.BINORMAL:
            has_corr = True
            code.add_line('bin_x, bin_y, bin_z, correct_v' + reader_code)

        # uv
        elif usage == fmt.TEXCOORD:
            _get_uv_code(
                code,
                ver,
                data_type,
                usage_index,
                reader_code,
                has_corr
            )

        # vertex color
        elif usage == fmt.COLOR:
            code.add_line('blue, green, red, sun' + reader_code)

            if data_type == fmt.D3DCOLOR:
                code.add_line('red /= 255')
                code.add_line('green /= 255')
                code.add_line('blue /= 255')
                code.add_line('sun /= 255')

            code.add_line('vb.color_light.append((red, green, blue))')
            code.add_line('vb.color_sun.append(sun)')

    exec(code.get_code())


def _import_vertices_d3d7(ver, reader, vb, verts_count, vert_fmt):
    code = 'for vertex_index in range({0}):\n'.format(verts_count)

    # position, normal, diffuse, tex coord

    if (vert_fmt & fmt.D3D7FVF.POSITION_MASK) == fmt.D3D7FVF.XYZ:
        code += '    pos = reader.getv3f()\n'
        code += '    vb.position.append(pos)\n'

    if vert_fmt & fmt.D3D7FVF.NORMAL:
        vb.float_normals = True
        code += '    norm_x, norm_y, norm_z = reader.getf("<3f")\n'
        code += '    vb.normal.append((norm_z, norm_x, norm_y))\n'

    if vert_fmt & fmt.D3D7FVF.DIFFUSE:
        code += '    red, green, blue, unknown = reader.getf("<4B")\n'
        code += '    vb.color_light.append((red/255, green/255, blue/255))\n'

    tex_count = (vert_fmt & fmt.D3D7FVF.TEXCOUNT_MASK) >> fmt.D3D7FVF.TEXCOUNT_SHIFT

    tex_uv_code = ''
    lmap_uv_code = ''

    # texture uv
    if tex_count:
        tex_uv_code += '    coord_u, coord_v = reader.getf("<2f")\n'
        tex_uv_code += '    vb.uv.append((coord_u, 1 - coord_v))\n'

    # light map uv
    if tex_count > 1:
        lmap_uv_code += '    lmap_u, lmap_v = reader.getf("<2f")\n'
        lmap_uv_code += '    vb.uv_lmap.append((lmap_u, 1 - lmap_v))\n'

    if tex_count > 2:
        for _ in range(tex_count - 2):
            lmap_uv_code += '    reader.skip(8)\n'

    if ver >= fmt.VERSION_8:
        code += tex_uv_code
        code += lmap_uv_code
    else:
        code += lmap_uv_code
        code += tex_uv_code

    exec(code)


def _import_vertex_buffer_declaration(packed_reader):
    usage_list = []

    while True:
        stream, offset = packed_reader.getf('<2H')
        type_, method, usage, usage_index = packed_reader.getf('<4B')

        if fmt.types[type_] == fmt.UNUSED:
            break

        usage_list.append((
            stream,
            offset,
            type_,
            method,
            usage,
            usage_index
        ))

    return usage_list


def _import_vertex_buffer_d3d9(packed_reader, ver):
    usage_list = _import_vertex_buffer_declaration(packed_reader)
    vertices_count = packed_reader.uint32()

    vertex_buffer = VertexBuffer()

    _import_vertices_d3d9(
        ver,
        packed_reader,
        vertex_buffer,
        vertices_count,
        usage_list
    )

    return vertex_buffer


def import_vertex_buffer_d3d7(packed_reader, ver):
    vertex_format = packed_reader.uint32()
    vertices_count = packed_reader.uint32()

    vertex_buffer = VertexBuffer()

    _import_vertices_d3d7(
        ver,
        packed_reader,
        vertex_buffer,
        vertices_count,
        vertex_format
    )

    return vertex_buffer


def _get_vbs_data(level, chunks, chunks_ids):
    vbs_data = chunks.pop(chunks_ids.VB, None)
    import_fun = _import_vertex_buffer_d3d9

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

    level.vertex_buffers = []
    for _ in range(buffers_count):
        vertex_buffer = import_fun(vbs_reader, level.xrlc_version)
        level.vertex_buffers.append(vertex_buffer)
