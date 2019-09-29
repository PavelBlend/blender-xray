import os, time

import bpy

from . import utils as level_utils, fmt, shaders, visuals, vb, ib, swi
from .. import xray_io, utils


class Level(object):
    def __init__(self):
        self.name = None
        self.xrlc_version = None
        self.xrlc_version_geom = None
        self.materials = None
        self.vertex_buffers = None
        self.indices_buffers = None
        self.swis = None
        self.loaded_geometry = {}
        self.hierrarhy_visuals = []
        self.visuals = []


def import_sectors(data):
    pass


def import_glows(data):
    pass


def import_light_dynamic(data):
    pass


def import_portals(data):
    pass


def check_version(xrlc_version):
    if xrlc_version not in fmt.SUPPORTED_VERSIONS:
        raise utils.AppError('Unsupported level version: {}'.format(
            xrlc_version
        ))


def import_header(data):
    packed_reader = xray_io.PackedReader(data)
    xrlc_version = packed_reader.getf('H')[0]
    check_version(xrlc_version)
    xrlc_quality = packed_reader.getf('H')[0]
    return xrlc_version


def get_chunks(chunked_reader):
    chunks = {}
    for chunk_id, chunk_data in chunked_reader:
        chunks[chunk_id] = chunk_data
    return chunks


def get_version(chunks):
    header_chunk_data = chunks.pop(fmt.Chunks.HEADER)
    xrlc_version = import_header(header_chunk_data)
    return xrlc_version


def import_geom(level, chunks, context):
    if level.xrlc_version == fmt.VERSION_14:
        geom_chunked_reader = level_utils.get_level_reader(
            context.file_path + os.extsep + 'geom'
        )
        geom_chunks = get_chunks(geom_chunked_reader)
        del geom_chunked_reader
        level.xrlc_version_geom = get_version(geom_chunks)
        chunks.update(geom_chunks)
        del geom_chunks


def import_level(level, context, chunks):
    for chunk_id, chunk_data in chunks.items():
        if chunk_id == fmt.Chunks.SHADERS:
            level.materials = shaders.import_shaders(context, chunk_data)
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
            level.vertex_buffers = vb.import_vertex_buffers(chunk_data)
        elif chunk_id == fmt.Chunks.IB:
            level.indices_buffers = ib.import_indices_buffers(chunk_data)
        elif chunk_id == fmt.Chunks.SWIS:
            level.swis = swi.import_slide_window_items(chunk_data)
        else:
            print('Unknown level chunk: {:x}'.format(chunk_id))

    visuals.import_visuals(visuals_chunk_data, level)
    visuals.import_hierrarhy_visuals(level)


def import_main(context, chunked_reader, level):
    chunks = get_chunks(chunked_reader)
    del chunked_reader
    level.xrlc_version = get_version(chunks)
    import_geom(level, chunks, context)
    import_level(level, context, chunks)


def import_file(context, operator):
    start_time = time.time()
    level = Level()
    chunked_reader = level_utils.get_level_reader(context.file_path)
    level.name = level_utils.get_level_name(context.file_path)
    import_main(context, chunked_reader, level)
    print('total time: {}'.format(time.time() - start_time))
