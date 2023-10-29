# standart modules
import os

# blender modules
import bpy
import mathutils

# addon modules
from . import header
from . import create
from . import shader
from . import visual
from . import vb
from . import ib
from . import swi
from . import cform
from . import geom
from . import light
from . import glow
from . import sector
from . import portal
from . import utility
from .. import fmt
from ... import ogf
from .... import text
from .... import log
from .... import utils
from .... import rw


class Level(object):
    def __init__(self):
        self.addon_version = utils.addon_version_number()
        self.name = None
        self.path = None
        self.file = None
        self.xrlc_version = None
        self.materials = None
        self.images = None
        self.shaders = None
        self.textures = None
        self.vertex_buffers = None
        self.indices_buffers = None
        self.swis = None
        self.loaded_geometry = {}
        self.loaded_fastpath_geometry = {}
        self.hierrarhy_visuals = []
        self.visuals = []
        self.collections = {}
        self.sectors_objects = {}


def _import_level(level, context, chunks):
    # find chunks ids
    if level.xrlc_version >= fmt.VERSION_13:
        chunks_ids = fmt.Chunks13
    elif level.xrlc_version == fmt.VERSION_12:
        chunks_ids = fmt.Chunks12
    elif level.xrlc_version in (fmt.VERSION_11, fmt.VERSION_10):
        chunks_ids = fmt.Chunks10
    elif level.xrlc_version == fmt.VERSION_9:
        chunks_ids = fmt.Chunks9
    elif level.xrlc_version == fmt.VERSION_8:
        chunks_ids = fmt.Chunks8
    elif level.xrlc_version == fmt.VERSION_5:
        chunks_ids = fmt.Chunks5
    elif level.xrlc_version == fmt.VERSION_4:
        chunks_ids = fmt.Chunks4

    # shaders
    shaders_data = chunks.pop(chunks_ids.SHADERS)
    level.materials, level.images = shader.import_shaders(
        level,
        context,
        shaders_data
    )

    # textures for 4, 5 versions
    if level.xrlc_version <= fmt.VERSION_5:
        tex_data = chunks.pop(chunks_ids.TEXTURES)
        shader.import_textures(level, tex_data)

    # vertex buffers
    vb_data = chunks.pop(chunks_ids.VB, None)
    vb_import_fun = vb.import_vertex_buffer

    if level.xrlc_version <= fmt.VERSION_8:
        vb_import_fun = vb.import_vertex_buffer_d3d7

    elif level.xrlc_version == fmt.VERSION_9:
        if not vb_data:
            vb_data = chunks.pop(chunks_ids.VB_OLD)
            vb_import_fun = vb.import_vertex_buffer_d3d7

    level.vertex_buffers = vb.import_vertex_buffers(
        vb_data,
        level,
        vb_import_fun
    )

    # index buffers
    if level.xrlc_version >= fmt.VERSION_9:
        ib_data = chunks.pop(chunks_ids.IB)
        level.indices_buffers = ib.import_indices_buffers(ib_data)

    # swis
    if level.xrlc_version >= fmt.VERSION_12:
        swis_data = chunks.pop(chunks_ids.SWIS, None)
        if swis_data:
            level.swis = swi.import_swi_buffers(swis_data)

    # create level object
    level_collection = create.create_level_collections(level)
    level_object = create.create_level_object(level, level_collection)

    # visuals
    visuals_data = chunks.pop(chunks_ids.VISUALS)
    visual.import_visuals(visuals_data, level)

    # sectors
    sectors_data = chunks.pop(chunks_ids.SECTORS)
    sector.import_sectors(sectors_data, level, level_object)

    # portals
    portals_data = chunks.pop(chunks_ids.PORTALS)
    portal.import_portals(portals_data, level, level_object)

    # glows
    glows_data = chunks.pop(chunks_ids.GLOWS)

    if level.xrlc_version >= fmt.VERSION_12:
        glow.import_glows_v12(glows_data, level, level_object)
    else:
        glow.import_glows_v5(glows_data, level, level_object)

    # lights
    lights_data = chunks.pop(chunks_ids.LIGHT_DYNAMIC)
    light.import_lights(lights_data, level, level_object)

    # cform
    if level.xrlc_version >= fmt.VERSION_10:
        cform_path = os.path.join(level.path, 'level.cform')
        cform_data = rw.utils.read_file(cform_path)
    else:
        cform_path = level.file
        cform_data = chunks.pop(chunks_ids.CFORM)

    cform.import_main(context, level, cform_path, cform_data)

    # print unreaded chunks
    for chunk_id, chunk_data in chunks.items():
        print('UNKNOWN LEVEL CHUNK: {0:#x}, SIZE = {1}'.format(
            chunk_id,
            len(chunk_data)
        ))


def _import_main(context, level):
    # level chunks
    level_reader = rw.utils.get_file_reader(level.file, chunked=True)
    chunks = rw.utils.get_reader_chunks(level_reader)

    # level version
    level.xrlc_version = header.get_version(chunks, context.filepath)

    # read level.geom
    geom_chunks = geom.read_geom(level, chunks, context)
    chunks.update(geom_chunks)

    # import level
    _import_level(level, context, chunks)


@log.with_context(name='import-game-level')
@utils.stats.timer
def import_file(context):
    utils.stats.status('Import File', context.filepath)

    level = Level()

    level.context = context
    level.name = utility.get_level_name(context.filepath)
    level.file = context.filepath
    level.path = os.path.dirname(context.filepath)

    context.level_name = level.name

    _import_main(context, level)
