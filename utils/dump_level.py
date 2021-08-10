import os
import optparse
import time

import utils

from io_scene_xray import xray_io


XRCL_CURRENT_VERSION = 10
XRCL_PRODUCTION_VERSION = 5
CFORM_CURRENT_VERSION = 2
XRAI_CURRENT_VERSION = 2
PORTAL_SIZE = 80
PORTAL_VERTICES_COUNT = 6
LIGHT_SIZE = 124
LIGHT_KEYFRAME_SIZE = 104
GLOW_SIZE = 24
PORTAL_INDEX_SIZE = 2
GLOW_INDEX_SIZE = 2
LIGHT_INDEX_SIZE = 2
OCCLUDER_SIZE = 76
OCCLUDER_VERTICES_COUNT = 6


class LevelChunks:
    HEADER = 1
    TEXTURES = 2
    SHADERS = 3
    VISUALS = 4
    VBUFFERS = 5
    CFORM = 6
    PORTALS = 7
    LIGHTS = 8
    LIGHT_KEYS = 9
    GLOWS = 10
    SECTORS = 11
    VISIBILITY = 12


class VisibilityChunks:
    HEADER = 1
    NODES = 2
    LIGHTS = 3
    GLOWS = 4
    OCCLUDERS = 5
    MAP = 6


class SectorChunks:
    PORTALS = 1
    ROOT = 2
    OCCLUDERS = 3
    GLOWS = 4
    LIGHTS = 5


class LightFlags:
    LMAPS = 1 << 15
    MODELS = 1 << 14
    PROCEDURAL = 1 << 13


class Direct3DFlexibleVertexFormat:
    # vertex data flags
    XYZ = 0x0002
    XYZRHW = 0x0004
    XYZB1 = 0x0006
    XYZB2 = 0x0008
    XYZB3 = 0x000a
    XYZB4 = 0x000c
    XYZB5 = 0x000e
    NORMAL = 0x0010
    PSIZE = 0x0020
    DIFFUSE = 0x0040
    SPECULAR = 0x0080
    # mask flags
    RESERVED0 = 0x0001
    RESERVED2 = 0xE000
    POSITION_MASK = 0x000E
    TEXCOUNT_MASK = 0x0f00
    # texture flags
    TEX0 = 0x0000
    TEX1 = 0x0100
    TEX2 = 0x0200
    TEX3 = 0x0300
    TEX4 = 0x0400
    TEX5 = 0x0500
    TEX6 = 0x0600
    TEX7 = 0x0700
    TEX8 = 0x0800
    # miscellaneous flags
    TEXCOUNT_SHIFT = 8
    LASTBETA_UBYTE4 = 0x1000


def read_sector_lights(data):
    packed_reader = xray_io.PackedReader(data)
    lights_count = len(data) // LIGHT_INDEX_SIZE
    for light_index in range(lights_count):
        light = packed_reader.getf('<H')[0]


def read_sector_glows(data):
    packed_reader = xray_io.PackedReader(data)
    glows_count = len(data) // GLOW_INDEX_SIZE
    for glow_index in range(glows_count):
        glow = packed_reader.getf('<H')[0]


def read_sector_occluders(data):
    data_size = len(data)
    if not data_size:
        return
    packed_reader = xray_io.PackedReader(data)
    occluders_count = data_size // OCCLUDER_SIZE
    for occluder_index in range(occluders_count):
        sector_index = packed_reader.getf('<H')[0]
        vertices_count = packed_reader.getf('<H')[0]
        for vertex_index in range(OCCLUDER_VERTICES_COUNT):
            vertex_coord = packed_reader.getf('<3I')


def read_sector_root(data):
    packed_reader = xray_io.PackedReader(data)
    root_visual = packed_reader.getf('<I')[0]


def read_sector_portals(data):
    packed_reader = xray_io.PackedReader(data)
    portals_count = len(data) // PORTAL_INDEX_SIZE
    for portal_index in range(portals_count):
        portal = packed_reader.getf('<H')[0]


def read_sector(data):
    chunked_reader = xray_io.ChunkedReader(data)
    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == SectorChunks.PORTALS:
            read_sector_portals(chunk_data)
        elif chunk_id == SectorChunks.ROOT:
            read_sector_root(chunk_data)
        elif chunk_id == SectorChunks.OCCLUDERS:
            read_sector_occluders(chunk_data)
        elif chunk_id == SectorChunks.GLOWS:
            read_sector_glows(chunk_data)
        elif chunk_id == SectorChunks.LIGHTS:
            read_sector_lights(chunk_data)
        else:
            print('unknown sector chunk:', chunk_id, 'size:', len(chunk_data))


def read_sectors(data):
    chunked_reader = xray_io.ChunkedReader(data)
    for sector_index, sector_data in chunked_reader:
        read_sector(sector_data)


def read_glows(data):
    packed_reader = xray_io.PackedReader(data)
    glows_count = len(data) // GLOW_SIZE
    for glow_index in range(glows_count):
        center = packed_reader.getf('<3f')
        radius = packed_reader.getf('<f')[0]
        texture_index = packed_reader.getf('<I')[0]
        shader_index = packed_reader.getf('<I')[0]


def read_light(packed_reader):
    light_source_type = packed_reader.getf('<I')[0]
    diffuse_color = packed_reader.getf('<4f')
    specular_color = packed_reader.getf('<4f')
    ambient_color = packed_reader.getf('<4f')
    position = packed_reader.getf('<3f')
    direction = packed_reader.getf('<3f')
    cutoff_range = packed_reader.getf('<f')[0]
    falloff = packed_reader.getf('<f')[0]
    constant_attenuation = packed_reader.getf('<f')[0]
    linear_attenuation = packed_reader.getf('<f')[0]
    quadratic_attenuation = packed_reader.getf('<f')[0]
    spotlight_cone_inner_angle_theta = packed_reader.getf('<f')[0]
    spotlight_cone_outer_angle_phi = packed_reader.getf('<f')[0]


def read_light_keys(data):
    packed_reader = xray_io.PackedReader(data)
    light_keys_count = len(data) // LIGHT_KEYFRAME_SIZE
    for light_keys_index in range(light_keys_count):
        read_light(packed_reader)


def read_lights(data):
    packed_reader = xray_io.PackedReader(data)
    lights_count = len(data) // LIGHT_SIZE
    for light_index in range(lights_count):
        read_light(packed_reader)
        dw_frame = packed_reader.getf('<I')[0]
        flags = packed_reader.getf('<H')[0]
        not_used = packed_reader.getf('<H')[0]
        for_light_maps = bool(flags & LightFlags.LMAPS)
        for_dynamic_models = bool(flags & LightFlags.MODELS)
        is_procedural = bool(flags & LightFlags.PROCEDURAL)
        current_time = packed_reader.getf('<f')[0]
        speed = packed_reader.getf('<f')[0]
        key_start = packed_reader.getf('<H')[0]
        key_count = packed_reader.getf('<H')[0]


def read_portals(data):
    packed_reader = xray_io.PackedReader(data)
    portals_count = len(data) // PORTAL_SIZE
    for portal_index in range(portals_count):
        sector_front = packed_reader.getf('<H')[0]
        sector_back = packed_reader.getf('<H')[0]
        used_vertices_count = packed_reader.getf('<I')[0]
        for vertex_index in range(PORTAL_VERTICES_COUNT):
            vertex_coord = packed_reader.getf('<3f')


def read_cform(data):
    start_time = time.time()
    packed_reader = xray_io.PackedReader(data)
    version = packed_reader.getf('<I')[0]
    if version != CFORM_CURRENT_VERSION:
        raise Exception('Unsupported cform version: {}'.format(version))
    vertices_count = packed_reader.getf('<I')[0]
    triangles_count = packed_reader.getf('<I')[0]
    bounding_box = packed_reader.getf('<6f')
    for vertex_index in range(vertices_count):
        vertex_coord = packed_reader.getf('<3f')
    for triangle_index in range(triangles_count):
        vertex_indices = packed_reader.getf('<3I')
        adjacent_triangles = packed_reader.getf('<3I')
        material = packed_reader.getf('<H')[0]
        sector = packed_reader.getf('<H')[0]
        dummy = packed_reader.getf('<I')[0]
    end_time = time.time()
    print('cform time:', round(end_time - start_time, 4), 'sec')


def print_fvf(fvf):
    print('{0:0>32b} VERTEX_FORMAT\n'.format(fvf))
    for flag_name in dir(Direct3DFlexibleVertexFormat):
        if flag_name.startswith('_'):
            continue
        flag_value = getattr(Direct3DFlexibleVertexFormat, flag_name)
        print('{0:0>32b} {1}'.format(flag_value, flag_name))


def read_vertex_buffers(data):
    start_time = time.time()
    packed_reader = xray_io.PackedReader(data)
    vertex_buffers_count = packed_reader.getf('<I')[0]
    FVF = Direct3DFlexibleVertexFormat
    cycle_code = 'for vertex_index in range(vertices_count):\n    '
    pos_code = "pos_x, poz_y, pos_z = packed_reader.getf('<3f')"
    norm_code = "norm_x, norm_y, norm_z = packed_reader.getf('<3f')"
    diffuse_code = "color_r, color_g, color_b, color_a = packed_reader.getf('<4B')"
    tex_uv_code = "tex_u, tex_v = packed_reader.getf('<2f')"
    lmap_uv_code = "lmap_u, lmap_v = packed_reader.getf('<2f')"
    uv_code = "coord_u, coord_v = packed_reader.getf('<2f')"
    for vertex_buffer_index in range(vertex_buffers_count):
        vertex_format = packed_reader.getf('<I')[0]
        vertices_count = packed_reader.getf('<I')[0]
        position_flags = vertex_format & FVF.POSITION_MASK
        tex_coord_count = (vertex_format & FVF.TEXCOUNT_MASK) >> FVF.TEXCOUNT_SHIFT
        code_list = []
        if position_flags == FVF.XYZ:
            code_list.append(pos_code)
        if vertex_format & FVF.NORMAL:
            code_list.append(norm_code)
        if vertex_format & FVF.DIFFUSE:
            code_list.append(diffuse_code)
        if tex_coord_count:
            if tex_coord_count == (FVF.TEX1 >> FVF.TEXCOUNT_SHIFT):
                code_list.append(tex_uv_code)
            elif tex_coord_count == (FVF.TEX2 >> FVF.TEXCOUNT_SHIFT):
                code_list.append(tex_uv_code)
                code_list.append(lmap_uv_code)
            else:
                print('\n    UV Warrning!\n')
                code_list.append(tex_uv_code)
                code_list.append(lmap_uv_code)
                for coord_index in range(2, tex_coord_count):
                    code_list.append(uv_code)
        vertex_code = '\n    '.join(code_list)
        vertices_code = cycle_code + vertex_code
        exec(vertices_code)
    end_time = time.time()
    print('vb time:', round(end_time - start_time, 4), 'sec')


def read_visual(data, chunks):
    chunked_reader = xray_io.ChunkedReader(data)
    for chunk_id, chunk_data in chunked_reader:
        chunks.add(chunk_id)


def read_visuals(data):
    chunks = set()
    chunked_reader = xray_io.ChunkedReader(data)
    for visual_index, visual_data in chunked_reader:
        read_visual(visual_data, chunks)
    for chunk_id in sorted(chunks):
        print(hex(chunk_id), end=' ')
    print()


def read_shaders(data):
    packed_reader = xray_io.PackedReader(data)
    shaders_count = packed_reader.getf('<I')[0]
    for shader_index in range(shaders_count):
        shader = packed_reader.gets()


def read_textures(data):
    packed_reader = xray_io.PackedReader(data)
    textures_count = packed_reader.getf('<I')[0]
    for texture_index in range(textures_count):
        texture = packed_reader.gets()


def read_header(data):
    packed_reader = xray_io.PackedReader(data)
    xrlc_version = packed_reader.getf('<I')[0]
    if xrlc_version != XRCL_PRODUCTION_VERSION:
        raise Exception('Unsupported level version: {}'.format(xrlc_version))
    name = packed_reader.getf('<124s')


def dump_level(level_data, print):
    chunked_reader = xray_io.ChunkedReader(level_data)
    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == LevelChunks.HEADER:
            read_header(chunk_data)
        elif chunk_id == LevelChunks.TEXTURES:
            read_textures(chunk_data)
        elif chunk_id == LevelChunks.SHADERS:
            read_shaders(chunk_data)
        elif chunk_id == LevelChunks.VISUALS:
            read_visuals(chunk_data)
        elif chunk_id == LevelChunks.VBUFFERS:
            read_vertex_buffers(chunk_data)
        elif chunk_id == LevelChunks.CFORM:
            read_cform(chunk_data)
        elif chunk_id == LevelChunks.PORTALS:
            read_portals(chunk_data)
        elif chunk_id == LevelChunks.LIGHTS:
            read_lights(chunk_data)
        elif chunk_id == LevelChunks.LIGHT_KEYS:
            read_light_keys(chunk_data)
        elif chunk_id == LevelChunks.GLOWS:
            read_glows(chunk_data)
        elif chunk_id == LevelChunks.SECTORS:
            read_sectors(chunk_data)
        else:
            print('unknown level chunk:', chunk_id, 'size:', len(chunk_data))


def main():
    parser = optparse.OptionParser(usage='Usage: dump_level.py <level-file>')
    (options, args) = parser.parse_args()
    if not args:
        parser.print_help()
    else:
        file_path = args[0]
        file_abs_path = os.path.abspath(file_path)
        if not os.path.exists(file_abs_path) or os.path.isdir(file_abs_path):
            print('File not found "{}"'.format(file_abs_path))
        else:
            level_data = utils.read_file(file_path)
            dump_level(level_data, print)


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print('total time:', round(end_time - start_time, 4), 'sec')
