from .. import xray_io
from . import fmt


def write_level_geom(chunked_writer):
    pass


def write_sectors():
    chunked_writer = xray_io.ChunkedWriter()
    return chunked_writer


def write_shaders():
    packed_writer = xray_io.PackedWriter()
    return packed_writer


def write_visuals():
    chunked_writer = xray_io.ChunkedWriter()
    return chunked_writer


def write_glow():
    packed_writer = xray_io.PackedWriter()
    return packed_writer


def write_light():
    packed_writer = xray_io.PackedWriter()
    return packed_writer


def write_portals():
    packed_writer = xray_io.PackedWriter()
    return packed_writer


def write_header():
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<H', fmt.VERSION_14)
    packed_writer.putf('<H', 0)    # quality
    return packed_writer


def write_level(chunked_writer):
    # header
    header_writer = write_header()
    chunked_writer.put(fmt.Chunks.HEADER, header_writer)
    del header_writer

    # portals
    portals_writer = write_portals()
    chunked_writer.put(fmt.Chunks.PORTALS, portals_writer)
    del portals_writer

    # light dynamic
    light_writer = write_light()
    chunked_writer.put(fmt.Chunks.LIGHT_DYNAMIC, light_writer)
    del light_writer

    # glow
    glows_writer = write_glow()
    chunked_writer.put(fmt.Chunks.GLOWS, glows_writer)
    del glows_writer

    # visuals
    visuals_writer = write_visuals()
    chunked_writer.put(fmt.Chunks.VISUALS, visuals_writer)
    del visuals_writer

    # shaders
    shaders_writer = write_shaders()
    chunked_writer.put(fmt.Chunks.SHADERS, shaders_writer)
    del shaders_writer

    # sectors
    sectors_writer = write_sectors()
    chunked_writer.put(fmt.Chunks.SECTORS, sectors_writer)
    del sectors_writer


def get_writer():
    chunked_writer = xray_io.ChunkedWriter()
    return chunked_writer


def export_file(level_object, file_path):
    level_chunked_writer = get_writer()
    write_level(level_chunked_writer)
    del level_chunked_writer

    level_geom_chunked_writer = get_writer()
    write_level_geom(level_geom_chunked_writer)
    del level_geom_chunked_writer

    print(file_path, level_object.name)
