# standart modules
import os

# blender modules
import bpy
import mathutils

# addon modules
from . import header
from . import create
from . import shaders
from . import visuals
from . import vb
from . import ib
from . import swi
from . import cform
from . import geom
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


INT_MAX = 2 ** 31 - 1


def import_light_dynamic(packed_reader, light_object):
    data = light_object.xray.level
    data.object_type = 'LIGHT_DYNAMIC'
    light_object.xray.is_level = True

    # controller id
    controller_id = packed_reader.uint32() # ???
    if controller_id > INT_MAX:
        controller_id = -1
    data.controller_id = controller_id

    position, direction = read_light(packed_reader, data)

    dir_vec = mathutils.Vector((direction[0], direction[2], direction[1]))
    euler = dir_vec.to_track_quat('Y', 'Z').to_euler('XYZ')
    light_object.location = position[0], position[2], position[1]
    light_object.rotation_euler = euler[0], euler[1], euler[2]


def read_light(packed_reader, data):
    light_type = packed_reader.uint32()    # type of light source
    if light_type > INT_MAX:
        light_type = -1
    data.light_type = light_type

    data.diffuse = packed_reader.getf('<4f')
    data.specular = packed_reader.getf('<4f')
    data.ambient = packed_reader.getf('<4f')

    position = packed_reader.getf('<3f')
    direction = packed_reader.getf('<3f')

    data.range_ = packed_reader.getf('<f')[0]    # cutoff range
    data.falloff = packed_reader.getf('<f')[0]
    data.attenuation_0 = packed_reader.getf('<f')[0]    # constant attenuation
    data.attenuation_1 = packed_reader.getf('<f')[0]    # linear attenuation
    data.attenuation_2 = packed_reader.getf('<f')[0]    # quadratic attenuation
    data.theta = packed_reader.getf('<f')[0]    # inner angle of spotlight cone
    data.phi = packed_reader.getf('<f')[0]    # outer angle of spotlight cone

    return position, direction


def import_light_dynamic_v8(packed_reader, light_object):
    light_object.xray.is_level = True
    data = light_object.xray.level
    data.object_type = 'LIGHT_DYNAMIC'

    position, direction = read_light(packed_reader, data)

    dw_frame = packed_reader.getf('<I')[0]
    flags = packed_reader.getf('<I')[0]
    affect_static = bool(flags & fmt.FLAG_AFFECT_STATIC)
    affect_dynamic = bool(flags & fmt.FLAG_AFFECT_DYNAMIC)
    procedural = bool(flags & fmt.FLAG_PROCEDURAL)

    name = packed_reader.getf('<{}s'.format(fmt.LIGHT_V8_NAME_LEN))

    if data.light_type == fmt.D3D_LIGHT_POINT:
        data.controller_id = 2
    elif data.light_type == fmt.D3D_LIGHT_DIRECTIONAL:
        data.controller_id = 1

    dir_vec = mathutils.Vector((direction[0], direction[2], direction[1]))
    euler = dir_vec.to_track_quat('Y', 'Z').to_euler('XYZ')
    light_object.location = position[0], position[2], position[1]
    light_object.rotation_euler = euler[0], euler[1], euler[2]


def import_light_dynamic_v5(packed_reader, light_object):
    light_object.xray.is_level = True
    data = light_object.xray.level
    data.object_type = 'LIGHT_DYNAMIC'

    position, direction = read_light(packed_reader, data)

    dw_frame, flags = packed_reader.getf('<2I')
    current_time, speed = packed_reader.getf('<2f')
    key_start, key_count = packed_reader.getf('<2H')

    if data.light_type == fmt.D3D_LIGHT_POINT:
        data.controller_id = 2
    elif data.light_type == fmt.D3D_LIGHT_DIRECTIONAL:
        data.controller_id = 1

    dir_vec = mathutils.Vector((direction[0], direction[2], direction[1]))
    euler = dir_vec.to_track_quat('Y', 'Z').to_euler('XYZ')
    light_object.location = position[0], position[2], position[1]
    light_object.rotation_euler = euler[0], euler[1], euler[2]


def create_light_object(light_index, collection):
    object_name = 'light_dynamic_{:0>3}'.format(light_index)
    if utils.version.IS_28:
        bpy_data = bpy.data.lights
    else:
        bpy_data = bpy.data.lamps
    light = bpy_data.new(object_name, 'SPOT')
    bpy_object = create.create_object(object_name, light)
    collection.objects.link(bpy_object)
    if not utils.version.IS_28:
        utils.version.link_object(bpy_object)
    return bpy_object


def create_lights_object(collection):
    object_name = 'light dynamic'
    bpy_object = create.create_object(object_name, None)
    collection.objects.link(bpy_object)
    if not utils.version.IS_28:
        utils.version.link_object(bpy_object)
    return bpy_object


def import_lights(data, level, level_object):
    packed_reader = rw.read.PackedReader(data)
    collection = level.collections[create.LEVEL_LIGHTS_COLLECTION_NAME]
    lights_object = create_lights_object(collection)
    lights_object.parent = level_object
    level_object.xray.level.lights_obj = lights_object.name

    if level.xrlc_version > fmt.VERSION_8:
        light_size = fmt.LIGHT_DYNAMIC_SIZE
        import_light_funct = import_light_dynamic
    elif level.xrlc_version == fmt.VERSION_8:
        light_size = fmt.LIGHT_DYNAMIC_SIZE_V8
        import_light_funct = import_light_dynamic_v8
    else:
        light_size = fmt.LIGHT_DYNAMIC_SIZE_V5
        import_light_funct = import_light_dynamic_v5

    light_count = len(data) // light_size
    for light_index in range(light_count):
        light_object = create_light_object(light_index, collection)
        import_light_funct(packed_reader, light_object)
        light_object.parent = lights_object


def import_level(level, context, chunks):
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
    level.materials, level.images = shaders.import_shaders(
        level,
        context,
        shaders_data
    )

    # textures for 4, 5 versions
    if level.xrlc_version <= fmt.VERSION_5:
        tex_data = chunks.pop(chunks_ids.TEXTURES)
        shaders.import_textures(level, tex_data)

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
    visuals.import_visuals(visuals_data, level)

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
    import_lights(lights_data, level, level_object)

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


def import_main(context, level):
    # level chunks
    level_reader = rw.utils.get_file_reader(level.file, chunked=True)
    chunks = rw.utils.get_reader_chunks(level_reader)

    # level version
    level.xrlc_version = header.get_version(chunks, context.filepath)

    # read level.geom
    geom_chunks = geom.read_geom(level, chunks, context)
    chunks.update(geom_chunks)

    # import level
    import_level(level, context, chunks)


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

    import_main(context, level)
