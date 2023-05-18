# standart modules
import os

# blender modules
import bpy
import mathutils

# addon modules
from . import create
from . import shaders
from . import visuals
from . import vb
from . import ib
from . import swi
from . import cform
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
        self.fastpath_vertex_buffers = None
        self.fastpath_indices_buffers = None
        self.fastpath_swis = None
        self.loaded_geometry = {}
        self.loaded_fastpath_geometry = {}
        self.hierrarhy_visuals = []
        self.visuals = []
        self.collections = {}
        self.sectors_objects = {}


def create_sector_object(sector_id, collection, sectors_object):
    object_name = 'sector_{:0>3}'.format(sector_id)
    bpy_object = create.create_object(object_name, None)
    bpy_object.parent = sectors_object
    collection.objects.link(bpy_object)
    if not utils.version.IS_28:
        utils.version.link_object(bpy_object)
    return bpy_object


def create_sectors_object(collection):
    object_name = 'sectors'
    bpy_object = create.create_object(object_name, None)
    collection.objects.link(bpy_object)
    if not utils.version.IS_28:
        utils.version.link_object(bpy_object)
    return bpy_object


def import_sector_portal(data):
    packed_reader = rw.read.PackedReader(data)
    portal_count = len(data) // fmt.SECTOR_PORTAL_SIZE
    for portal_index in range(portal_count):
        portal = packed_reader.getf('<H')[0]


def import_sector_root(data):
    packed_reader = rw.read.PackedReader(data)
    root = packed_reader.uint32()
    return root


def import_sector(data, level, sector_object):
    chunked_reader = rw.read.ChunkedReader(data)
    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == fmt.SectorChunks.PORTALS:
            import_sector_portal(chunk_data)
        elif chunk_id == fmt.SectorChunks.ROOT:
            root_visual_index = import_sector_root(chunk_data)
            level.visuals[root_visual_index].parent = sector_object
        else:
            print('UNKNOWN LEVEL SECTOR CHUNK: {0:#x}, SIZE = {1}'.format(
                chunk_id, len(chunk_data)
            ))


def import_sectors(data, level, level_object):
    chunked_reader = rw.read.ChunkedReader(data)
    collection = level.collections[create.LEVEL_SECTORS_COLLECTION_NAME]
    sectors_object = create_sectors_object(collection)
    sectors_object.parent = level_object
    for sector_id, sector_data in chunked_reader:
        sector_object = create_sector_object(
            sector_id, collection, sectors_object
        )
        level.sectors_objects[sector_id] = sector_object
        import_sector(sector_data, level, sector_object)


def generate_glow_mesh_data(radius):
    vertices = []
    for side_index in range(2):    # two sided mesh
        vertices.extend((
            # XZ-plane
            (radius, 0.0, -radius),
            (radius, 0.0, radius),
            (-radius, 0.0, radius),
            (-radius, 0.0, -radius),
            # YZ-plane
            (0.0, radius, -radius),
            (0.0, radius, radius),
            (0.0, -radius, radius),
            (0.0, -radius, -radius),
            # XY-plane
            (radius, -radius, 0.0),
            (radius, radius, 0.0),
            (-radius, radius, 0.0),
            (-radius, -radius, 0.0)
        ))

    faces = (
        # front side
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (8, 9, 10, 11),
        # back side
        (15, 14, 13, 12),
        (19, 18, 17, 16),
        (23, 22, 21, 20),
    )
    uv_face = (
        (1.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
        (0.0, 0.0),
    )

    uvs = []
    for face_index in range(6):
        uvs.extend(uv_face)

    return vertices, faces, uvs


def create_glow_mesh(name, vertices, faces, uvs, material, image):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, (), faces)
    if utils.version.IS_28:
        uv_layer = mesh.uv_layers.new(name='Texture')
    else:
        uv_texture = mesh.uv_textures.new(name='Texture')
        uv_layer = mesh.uv_layers[uv_texture.name]
        for tex_poly in uv_texture.data:
            tex_poly.image = image
    for uv_index, data in enumerate(uv_layer.data):
        data.uv = uvs[uv_index]
    mesh.materials.append(material)
    if utils.version.IS_28:
        material.use_backface_culling = False
        material.blend_method = 'BLEND'
    return mesh


def create_glow_object(
        glow_index,
        position,
        radius,
        shader_index,
        materials,
        images
    ):
    object_name = 'glow_{:0>3}'.format(glow_index)
    vertices, faces, uvs = generate_glow_mesh_data(radius)
    material = materials[shader_index]
    image = images[shader_index]
    mesh = create_glow_mesh(
        object_name,
        vertices,
        faces,
        uvs,
        material,
        image
    )
    glow_object = create.create_object(object_name, mesh)
    glow_object.location = position[0], position[2], position[1]
    return glow_object


def create_glow_object_v5(
        level,
        glow_index,
        position,
        radius,
        shader_index,
        texture_index
    ):
    object_name = 'glow_{:0>3}'.format(glow_index)
    vertices, faces, uvs = generate_glow_mesh_data(radius)
    material = ogf.imp.material.get_level_material(
        level,
        shader_index,
        texture_index
    )
    image = level.images[texture_index]
    mesh = create_glow_mesh(
        object_name,
        vertices,
        faces,
        uvs,
        material,
        image
    )
    glow_object = create.create_object(object_name, mesh)
    glow_object.location = position[0], position[2], position[1]
    return glow_object


def import_glow(packed_reader, glow_index, materials, images):
    position = packed_reader.getf('<3f')
    radius = packed_reader.getf('<f')[0]
    shader_index = packed_reader.getf('<H')[0]
    glow_object = create_glow_object(
        glow_index,
        position,
        radius,
        shader_index,
        materials,
        images
    )
    return glow_object


def import_glow_v5(level, packed_reader, glow_index):
    position = packed_reader.getf('<3f')
    radius = packed_reader.getf('<f')[0]
    texture_index = packed_reader.uint32()
    shader_index = packed_reader.uint32()
    glow_object = create_glow_object_v5(
        level, glow_index, position, radius,
        shader_index, texture_index
    )
    return glow_object


def create_glows_object(collection):
    object_name = 'glows'
    bpy_object = create.create_object(object_name, None)
    collection.objects.link(bpy_object)
    if not utils.version.IS_28:
        utils.version.link_object(bpy_object)
    return bpy_object


def import_glows(data, level):
    packed_reader = rw.read.PackedReader(data)
    glows_count = len(data) // fmt.GLOW_SIZE
    collection = level.collections[create.LEVEL_GLOWS_COLLECTION_NAME]
    glows_object = create_glows_object(collection)
    materials = level.materials
    images = level.images

    for glow_index in range(glows_count):
        glow_object = import_glow(
            packed_reader,
            glow_index,
            materials,
            images
        )
        glow_object.parent = glows_object
        glow_object.xray.version = level.addon_version
        glow_object.xray.isroot = False
        collection.objects.link(glow_object)
        if not utils.version.IS_28:
            utils.version.link_object(glow_object)

    return glows_object


def import_glows_v5(data, level):
    packed_reader = rw.read.PackedReader(data)
    glows_count = len(data) // fmt.GLOW_SIZE_V5
    collection = level.collections[create.LEVEL_GLOWS_COLLECTION_NAME]
    glows_object = create_glows_object(collection)

    for glow_index in range(glows_count):
        glow_object = import_glow_v5(level, packed_reader, glow_index)
        glow_object.parent = glows_object
        glow_object.xray.version = level.addon_version
        glow_object.xray.isroot = False
        collection.objects.link(glow_object)
        if not utils.version.IS_28:
            utils.version.link_object(glow_object)

    return glows_object


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

    # light type
    light_type = packed_reader.uint32() # ???
    if light_type > INT_MAX:
        light_type = -1
    data.light_type = light_type

    data.diffuse = packed_reader.getf('<4f')
    data.specular = packed_reader.getf('<4f')
    data.ambient = packed_reader.getf('<4f')
    position = packed_reader.getf('<3f')
    direction = packed_reader.getf('<3f')
    data.range_ = packed_reader.getf('<f')[0]
    data.falloff = packed_reader.getf('<f')[0]
    data.attenuation_0 = packed_reader.getf('<f')[0]
    data.attenuation_1 = packed_reader.getf('<f')[0]
    data.attenuation_2 = packed_reader.getf('<f')[0]
    data.theta = packed_reader.getf('<f')[0]
    data.phi = packed_reader.getf('<f')[0]

    dir_vec = mathutils.Vector((direction[0], direction[2], direction[1]))
    euler = dir_vec.to_track_quat('Y', 'Z').to_euler('XYZ')
    light_object.location = position[0], position[2], position[1]
    light_object.rotation_euler = euler[0], euler[1], euler[2]


def import_light_dynamic_v8(packed_reader, light_object):
    data = light_object.xray.level
    data.object_type = 'LIGHT_DYNAMIC'
    light_object.xray.is_level = True
    data.light_type = packed_reader.uint32() # ???
    data.diffuse = packed_reader.getf('<4f')
    data.specular = packed_reader.getf('<4f')
    data.ambient = packed_reader.getf('<4f')
    position = packed_reader.getf('<3f')
    direction = packed_reader.getf('<3f')
    data.range_ = packed_reader.getf('<f')[0]
    data.falloff = packed_reader.getf('<f')[0]
    data.attenuation_0 = packed_reader.getf('<f')[0]
    data.attenuation_1 = packed_reader.getf('<f')[0]
    data.attenuation_2 = packed_reader.getf('<f')[0]
    data.theta = packed_reader.getf('<f')[0]
    data.phi = packed_reader.getf('<f')[0]
    unknown = packed_reader.getf('<2I')
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
    data = light_object.xray.level
    data.object_type = 'LIGHT_DYNAMIC'
    light_object.xray.is_level = True
    data.light_type = packed_reader.uint32() # ???
    data.diffuse = packed_reader.getf('<4f')
    data.specular = packed_reader.getf('<4f')
    data.ambient = packed_reader.getf('<4f')
    position = packed_reader.getf('<3f')
    direction = packed_reader.getf('<3f')
    data.range_ = packed_reader.getf('<f')[0]
    data.falloff = packed_reader.getf('<f')[0]
    data.attenuation_0 = packed_reader.getf('<f')[0]
    data.attenuation_1 = packed_reader.getf('<f')[0]
    data.attenuation_2 = packed_reader.getf('<f')[0]
    data.theta = packed_reader.getf('<f')[0]
    data.phi = packed_reader.getf('<f')[0]
    unknown = packed_reader.getf('<5I')

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


def import_lights_dynamic(data, level):
    packed_reader = rw.read.PackedReader(data)
    collection = level.collections[create.LEVEL_LIGHTS_COLLECTION_NAME]
    lights_dynamic_object = create_lights_object(collection)

    if level.xrlc_version >= fmt.VERSION_8:
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
        light_object.parent = lights_dynamic_object

    return lights_dynamic_object


def create_portal(portal_index, verts, collection):
    object_name = 'portal_{:0>3}'.format(portal_index)

    faces = [list(range(len(verts))), ]
    portal_mesh = bpy.data.meshes.new(object_name)
    portal_mesh.from_pydata(verts, (), faces)

    portal_obj = create.create_object(object_name, portal_mesh)

    collection.objects.link(portal_obj)
    if not utils.version.IS_28:
        utils.version.link_object(portal_obj)

    return portal_obj


def import_portal(packed_reader, portal_index, collection, level):
    sector_front = packed_reader.getf('<H')[0]
    sector_back = packed_reader.getf('<H')[0]

    if level.xrlc_version <= fmt.VERSION_5:
        used_verts_count = packed_reader.uint32()

    verts = []
    for vertex_index in range(fmt.PORTAL_VERTEX_COUNT):
        coord_x, coord_y, coord_z = packed_reader.getf('<3f')
        verts.append((coord_x, coord_z, coord_y))

    if level.xrlc_version >= fmt.VERSION_8:
        used_verts_count = packed_reader.uint32()

    verts = verts[ : used_verts_count]

    portal_obj = create_portal(portal_index, verts, collection)

    xray = portal_obj.xray
    xray.version = level.addon_version
    xray.isroot = False
    xray.is_level = True
    xray.level.object_type = 'PORTAL'
    xray.level.sector_front = level.sectors_objects[sector_front].name
    xray.level.sector_back = level.sectors_objects[sector_back].name

    return portal_obj


def import_portals(data, level):
    portal_reader = rw.read.PackedReader(data)

    collection = level.collections[create.LEVEL_PORTALS_COLLECTION_NAME]
    portals_object = create.create_object('portals', None)
    collection.objects.link(portals_object)

    if not utils.version.IS_28:
        utils.version.link_object(portals_object)

    portals_count = len(data) // fmt.PORTAL_SIZE
    for portal_index in range(portals_count):
        portal_object = import_portal(
            portal_reader,
            portal_index,
            collection,
            level
        )
        portal_object.parent = portals_object

    return portals_object


def get_chunks(chunked_reader):
    return {chunk_id: chunk_data for chunk_id, chunk_data in chunked_reader}


def get_version(data, file):
    header_reader = rw.read.PackedReader(data)

    xrlc_version = header_reader.getf('<H')[0]
    if not xrlc_version in fmt.SUPPORTED_VERSIONS:
        raise log.AppError(
            text.error.level_unsupport_ver,
            log.props(
                version=xrlc_version,
                file=file
            )
        )

    xrlc_quality = header_reader.getf('<H')[0]

    return xrlc_version


def read_geomx(level, context):
    geomx_chunks = {}

    if level.xrlc_version == fmt.VERSION_14:
        geomx_path = context.filepath + os.extsep + 'geomx'

        if os.path.exists(geomx_path):
            geomx_reader = utility.get_level_reader(geomx_path)
            geomx_chunks = get_chunks(geomx_reader)
            get_version(geomx_chunks.pop(fmt.HEADER), geomx_path)

    return geomx_chunks


def read_geom(level, chunks, context):
    geom_chunks = {}

    if level.xrlc_version >= fmt.VERSION_13:
        geom_path = context.filepath + os.extsep + 'geom'
        geom_reader = utility.get_level_reader(geom_path)
        geom_chunks = get_chunks(geom_reader)
        get_version(geom_chunks.pop(fmt.HEADER), geom_path)

    return geom_chunks


def import_level(level, context, chunks, geomx_chunks):
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
            level.swis = swi.import_slide_window_items(swis_data)

    # fastpath geometry
    if level.xrlc_version == fmt.VERSION_14 and geomx_chunks:

        # fastpath vertex buffers
        vb_fp_data = geomx_chunks.pop(chunks_ids.VB)
        level.fastpath_vertex_buffers = vb.import_vertex_buffers(
            vb_fp_data,
            level,
            vb.import_vertex_buffer
        )

        # fastpath index buffers
        ib_fp_data = geomx_chunks.pop(chunks_ids.IB)
        level.fastpath_indices_buffers = ib.import_indices_buffers(ib_fp_data)

        # fastpath swis
        swis_fp_data = geomx_chunks.pop(chunks_ids.SWIS)
        level.fastpath_swis = swi.import_slide_window_items(swis_fp_data)

    # create level object
    level_collection = create.create_level_collections(level)
    level_object = create.create_level_object(level, level_collection)

    # visuals
    visuals_data = chunks.pop(chunks_ids.VISUALS)
    visuals.import_visuals(visuals_data, level)
    visuals.import_hierrarhy_visuals(level)

    # sectors
    sectors_data = chunks.pop(chunks_ids.SECTORS)
    import_sectors(sectors_data, level, level_object)

    # portals
    portals_data = chunks.pop(chunks_ids.PORTALS)
    portals_object = import_portals(portals_data, level)
    portals_object.parent = level_object

    # glows
    glows_data = chunks.pop(chunks_ids.GLOWS)

    if level.xrlc_version >= fmt.VERSION_12:
        glows_object = import_glows(glows_data, level)
    else:
        glows_object = import_glows_v5(glows_data, level)

    glows_object.parent = level_object

    # lights
    lights_data = chunks.pop(chunks_ids.LIGHT_DYNAMIC)
    lights_object = import_lights_dynamic(lights_data, level)
    lights_object.parent = level_object

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

    return cform_path, cform_data


def import_main(context, chunked_reader, level):
    # level chunks
    chunks = get_chunks(chunked_reader)

    # level version
    level.xrlc_version = get_version(chunks.pop(fmt.HEADER), context.filepath)

    # read level.geom
    geom_chunks = read_geom(level, chunks, context)
    chunks.update(geom_chunks)

    # read level.geomx
    geomx_chunks = read_geomx(level, context)

    # import level
    import_level(level, context, chunks, geomx_chunks)


@log.with_context(name='import-game-level')
def import_file(context):
    level = Level()

    level.context = context
    level.name = utility.get_level_name(context.filepath)
    level.file = context.filepath
    level.path = os.path.dirname(context.filepath)

    level_reader = rw.utils.get_file_reader(level.file, chunked=True)

    import_main(context, level_reader, level)
