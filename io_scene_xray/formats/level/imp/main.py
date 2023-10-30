# standart modules
import os

# blender modules
import bpy

# addon modules
from . import header
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
from . import name
from .. import fmt
from .... import log
from .... import text
from .... import utils
from .... import rw


class Level:
    def __init__(self):
        self.addon_version = utils.addon_version_number()

        self.name = None
        self.file = None
        self.path = None
        self.context = None

        self.xrlc_version = None

        self.materials = None
        self.images = None
        self.shaders = None
        self.textures = None
        self.shaders_or_textures = None

        self.vertex_buffers = None
        self.indices_buffers = None
        self.swis = None

        self.visuals = []
        self.hierrarhy_visuals = []

        self.collections = {}
        self.sectors_objects = {}
        self.loaded_geometry = {}


def _get_level_chunks_ids(level):
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

    return chunks_ids


def _create_level_object(level, level_collection):
    level_object = utils.obj.create_object(level.name, None, False)

    level_collection.objects.link(level_object)
    if not utils.version.IS_28:
        utils.version.link_object(level_object)

    level_object.xray.is_level = True
    level_object.xray.level.object_type = 'LEVEL'

    return level_object


def _create_level_collections(level):
    if utils.version.IS_28:
        scene_collection = bpy.context.scene.collection
    else:
        scene_collection = None

    # create main collection
    level_collection = utils.version.create_collection(
        level.name,
        scene_collection
    )
    level.collections[name.LEVEL_MAIN_COLLECTION_NAME] = level_collection

    # create level collections
    for collection_name in name.LEVEL_COLLECTION_NAMES:
        collection = utils.version.create_collection(
            collection_name,
            level_collection
        )
        level.collections[collection_name] = collection

    # create visuals collections
    visuals_collection = level.collections[name.LEVEL_VISUALS_COLLECTION_NAME]
    for collection_name in name.LEVEL_VISUALS_COLLECTION_NAMES:
        collection = utils.version.create_collection(
            collection_name,
            visuals_collection
        )
        level.collections[collection_name] = collection

    return level_collection


def _import_level(level, context, chunks, chunks_ids, level_object):
    # shaders
    shader.import_shaders(level, context, chunks, chunks_ids)

    # textures
    shader.import_textures(level, chunks, chunks_ids)

    # vertices
    vb.import_vertex_buffers(level, chunks, chunks_ids)

    # indices
    ib.import_indices_buffers(level, chunks, chunks_ids)

    # swis
    swi.import_swi_buffers(level, chunks, chunks_ids)

    # visuals
    visual.import_visuals(level, chunks, chunks_ids)

    # sectors
    sector.import_sectors(level, level_object, chunks, chunks_ids)

    # portals
    portal.import_portals(level, level_object, chunks, chunks_ids)

    # glows
    glow.import_glows(level, level_object, chunks, chunks_ids)

    # lights
    light.import_lights(level, level_object, chunks, chunks_ids)

    # cforms
    cform.import_cform(context, level, chunks, chunks_ids)


def _import_main(context, level):
    # level chunks
    chunks = rw.utils.get_file_chunks(level.file)

    # level version
    level.xrlc_version = header.get_version(chunks, context.filepath)

    # read level.geom
    geom.read_geom(level, chunks, context)

    # get chunks
    chunks_ids = _get_level_chunks_ids(level)

    # create level object
    level_collection = _create_level_collections(level)
    level_object = _create_level_object(level, level_collection)

    # import level
    _import_level(level, context, chunks, chunks_ids, level_object)


def _get_level_name(file_path):
    dir_path = os.path.dirname(file_path)
    return os.path.basename(dir_path)


def _check_levels_folder(context):
    if not context.lvl_mod_folder and not context.lvl_folder:
        log.warn(text.warn.level_folder_not_spec)


@log.with_context(name='import-game-level')
@utils.stats.timer
def import_file(imp_ctx):
    utils.stats.status('Import File', imp_ctx.filepath)

    level = Level()

    level.context = imp_ctx
    level.file = imp_ctx.filepath
    level.name = _get_level_name(imp_ctx.filepath)
    level.path = os.path.dirname(imp_ctx.filepath)

    imp_ctx.level_path = os.path.dirname(level.file)
    imp_ctx.level_name = level.name

    _check_levels_folder(imp_ctx)
    _import_main(imp_ctx, level)
