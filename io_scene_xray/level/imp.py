import bpy

from . import utils as level_utils, fmt, shaders, visuals
from .. import xray_io, utils


def import_slide_window_items(data):
    pass


def import_indices_buffer(data):
    pass


def import_vertex_buffer(data):
    pass


def import_sectors(data):
    pass


def import_glows(data):
    pass


def import_light_dynamic(data):
    pass


def import_portals(data):
    pass


def import_header(data):
    packed_reader = xray_io.PackedReader(data)
    xrlc_version = packed_reader.getf('H')[0]
    if xrlc_version not in fmt.SUPPORTED_VERSIONS:
        raise utils.AppError('Unsupported level version: {}'.format(
            xrlc_version
        ))
    xrlc_quality = packed_reader.getf('H')[0]


def import_main(context, chunked_reader, level_name):
    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == fmt.Chunks.HEADER:
            import_header(chunk_data)
        elif chunk_id == fmt.Chunks.SHADERS:
            materials = shaders.import_shaders(context, chunk_data)
        elif chunk_id == fmt.Chunks.VISUALS:
            visuals_chunk_data = chunk_data
        elif chunk_id == fmt.Chunks.PORTALS:
            import_portals(chunk_data)
        elif chunk_id == fmt.Chunks.LIGHT_DYNAMIC:
            import_light_dynamic(chunk_data)
        elif chunk_id == fmt.Chunks.GLOWS:
            import_glows(chunk_data)
        elif chunk_id == fmt.Chunks.SECTORS:
            import_sectors(chunk_data)
        elif chunk_id == fmt.Chunks.VB:
            import_vertex_buffer(chunk_data)
        elif chunk_id == fmt.Chunks.IB:
            import_indices_buffer(chunk_data)
        elif chunk_id == fmt.Chunks.SWIS:
            import_slide_window_items(chunk_data)
        else:
            print('Unknown level chunk: {:x}'.format(chunk_id))

    visuals.import_visuals(visuals_chunk_data, materials)


def import_file(context, operator):
    chunked_reader = level_utils.get_level_reader(context.file_path)
    level_name = level_utils.get_level_name(context.file_path)
    import_main(context, chunked_reader, level_name)
