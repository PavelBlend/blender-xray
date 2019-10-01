import os, time

import bpy

from . import utils as level_utils, create, fmt, shaders, visuals, vb, ib, swi
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
        self.collections = {}


def create_sector_object(sector_id, level_collection, sectors_object):
    object_name = 'sector_{:0>3}'.format(sector_id)
    bpy_object = create.create_object(object_name, None)
    bpy_object.parent = sectors_object
    level_collection.objects.link(bpy_object)
    return bpy_object


def create_sectors_object(level_collection):
    object_name = 'sectors'
    bpy_object = create.create_object(object_name, None)
    level_collection.objects.link(bpy_object)
    return bpy_object


def import_sector_portal(data):
    packed_reader = xray_io.PackedReader(data)
    portal_count = len(data) // fmt.SECTOR_PORTAL_SIZE

    for portal_index in range(portal_count):
        portal = packed_reader.getf('H')[0]


def import_sector_root(data):
    packed_reader = xray_io.PackedReader(data)
    root = packed_reader.getf('I')[0]
    return root


def import_sector(data, level, sector_object):
    chunked_reader = xray_io.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == fmt.SectorChunks.PORTALS:
            import_sector_portal(chunk_data)
        elif chunk_id == fmt.SectorChunks.ROOT:
            root_visual_index = import_sector_root(chunk_data)
            level.visuals[root_visual_index].parent = sector_object
        else:
            print('UNKNOW LEVEL SECTOR CHUNK: {0:#x}'.format(chunk_id))


def import_sectors(data, level, level_collection, level_object):
    chunked_reader = xray_io.ChunkedReader(data)
    sectors_object = create_sectors_object(level_collection)
    sectors_object.parent = level_object

    for sector_id, sector_data in chunked_reader:
        sector_object = create_sector_object(
            sector_id, level_collection, sectors_object
        )
        import_sector(sector_data, level, sector_object)


def generate_glow_mesh_data(radius):
    vertices = (
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
    )
    faces = (
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (8, 9, 10, 11)
    )
    uv_face = (
        (1.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
        (0.0, 0.0),
    )
    uvs = []
    for face_index in range(3):
        uvs.extend(uv_face)
    return vertices, faces, uvs


def create_glow_mesh(name, vertices, faces, uvs):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, (), faces)
    uv_layer = mesh.uv_layers.new(name='Texture')
    for uv_index, data in enumerate(uv_layer.data):
        data.uv = uvs[uv_index]
    return mesh


def create_glow_object(glow_index, position, radius, shader_index, materials):
    object_name = 'glow_{:0>3}'.format(glow_index)
    vertices, faces, uvs = generate_glow_mesh_data(radius)
    mesh = create_glow_mesh(object_name, vertices, faces, uvs)
    material = materials[shader_index]
    material.use_backface_culling = False
    material.blend_method = 'BLEND'
    mesh.materials.append(material)
    glow_object = create.create_object(object_name, mesh)
    glow_object.location = position[0], position[2], position[1]
    return glow_object


def import_glow(packed_reader, glow_index, materials):
    position = packed_reader.getf('3f')
    radius = packed_reader.getf('f')[0]
    shader_index = packed_reader.getf('H')[0]
    glow_object = create_glow_object(
        glow_index, position, radius, shader_index, materials
    )
    return glow_object


def create_glows_object(level_collection):
    object_name = 'glows'
    bpy_object = create.create_object(object_name, None)
    level_collection.objects.link(bpy_object)
    return bpy_object


def import_glows(data, materials, level_collection):
    packed_reader = xray_io.PackedReader(data)
    glows_count = len(data) // fmt.GLOW_SIZE
    glows_object = create_glows_object(level_collection)

    for glow_index in range(glows_count):
        glow_object = import_glow(packed_reader, glow_index, materials)
        glow_object.parent = glows_object
        level_collection.objects.link(glow_object)

    return glows_object


def import_light_dynamic(packed_reader, light_object):
    controller_id = packed_reader.getf('I')[0] # ???
    light_type = packed_reader.getf('I')[0] # ???
    diffuse = packed_reader.getf('4f')
    specular = packed_reader.getf('4f')
    ambient = packed_reader.getf('4f')
    position = packed_reader.getf('3f')
    direction = packed_reader.getf('3f')
    range_ = packed_reader.getf('f')[0]
    falloff = packed_reader.getf('f')[0]
    attenuation_0 = packed_reader.getf('f')[0]
    attenuation_1 = packed_reader.getf('f')[0]
    attenuation_2 = packed_reader.getf('f')[0]
    theta = packed_reader.getf('f')[0]
    phi = packed_reader.getf('f')[0]

    light_object.location = position[0], position[2], position[1]
    light_object.rotation_euler = direction[0], direction[2], direction[1]


def create_light_object(light_index, level_collection):
    object_name = 'light_dynamic_{:0>3}'.format(light_index)
    light = bpy.data.lights.new(object_name, 'SPOT')
    bpy_object = create.create_object(object_name, light)
    level_collection.objects.link(bpy_object)
    return bpy_object


def create_lights_object(level_collection):
    object_name = 'light dynamic'
    bpy_object = create.create_object(object_name, None)
    level_collection.objects.link(bpy_object)
    return bpy_object


def import_lights_dynamic(data, level_collection):
    packed_reader = xray_io.PackedReader(data)
    light_count = len(data) // fmt.LIGHT_DYNAMIC_SIZE
    lights_dynamic_object = create_lights_object(level_collection)

    for light_index in range(light_count):
        light_object = create_light_object(light_index, level_collection)
        import_light_dynamic(packed_reader, light_object)
        light_object.parent = lights_dynamic_object

    return lights_dynamic_object


def generate_portal_face(vertices):
    face = list(range(len(vertices)))
    return [face, ]


def create_portal_mesh(object_name, vertices):
    faces = generate_portal_face(vertices)
    mesh = bpy.data.meshes.new(object_name)
    mesh.from_pydata(vertices, (), faces)
    return mesh


def create_portal(portal_index, vertices, level_collection):
    object_name = 'portal_{:0>3}'.format(portal_index)
    object_data = create_portal_mesh(object_name, vertices)
    portal_object = create.create_object(object_name, object_data)
    level_collection.objects.link(portal_object)
    return portal_object


def import_portal(packed_reader, portal_index, level_collection):
    sector_front = packed_reader.getf('H')[0]
    sector_back = packed_reader.getf('H')[0]
    vertices = []

    for vertex_index in range(fmt.PORTAL_VERTEX_COUNT):
        coord_x, coord_y, coord_z = packed_reader.getf('fff')
        vertices.append((coord_x, coord_z, coord_y))

    used_vertices_count = packed_reader.getf('I')[0]
    vertices = vertices[ : used_vertices_count]
    portal_object = create_portal(portal_index, vertices, level_collection)
    return portal_object


def import_portals(data, level_collection):
    packed_reader = xray_io.PackedReader(data)
    portals_count = len(data) // fmt.PORTAL_SIZE
    portals_object = create.create_object('portals', None)

    for portal_index in range(portals_count):
        portal_object = import_portal(
            packed_reader, portal_index, level_collection
        )
        portal_object.parent = portals_object

    return portals_object


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
    shaders_chunk_data = chunks.pop(fmt.Chunks.SHADERS)
    level.materials = shaders.import_shaders(context, shaders_chunk_data)
    del shaders_chunk_data

    vb_chunk_data = chunks.pop(fmt.Chunks.VB)
    level.vertex_buffers = vb.import_vertex_buffers(vb_chunk_data)
    del vb_chunk_data

    ib_chunk_data = chunks.pop(fmt.Chunks.IB)
    level.indices_buffers = ib.import_indices_buffers(ib_chunk_data)
    del ib_chunk_data

    swis_chunk_data = chunks.pop(fmt.Chunks.SWIS)
    level.swis = swi.import_slide_window_items(swis_chunk_data)
    del swis_chunk_data

    level_collection = create.create_level_collections(level)
    level_object = create.create_level_objects(level, level_collection)

    visuals_chunk_data = chunks.pop(fmt.Chunks.VISUALS)
    visuals.import_visuals(visuals_chunk_data, level)
    visuals.import_hierrarhy_visuals(level)
    del visuals_chunk_data

    sectors_chunk_data = chunks.pop(fmt.Chunks.SECTORS)
    import_sectors(sectors_chunk_data, level, level_collection, level_object)
    del sectors_chunk_data

    portals_chunk_data = chunks.pop(fmt.Chunks.PORTALS)
    portals_object = import_portals(portals_chunk_data, level_collection)
    del portals_chunk_data

    level_collection.objects.link(portals_object)
    portals_object.parent = level_object

    glows_chunk_data = chunks.pop(fmt.Chunks.GLOWS)
    glows_object = import_glows(
        glows_chunk_data, level.materials, level_collection
    )
    del glows_chunk_data
    glows_object.parent = level_object

    light_chunk_data = chunks.pop(fmt.Chunks.LIGHT_DYNAMIC)
    lights_dynamic_object = import_lights_dynamic(
        light_chunk_data, level_collection
    )
    lights_dynamic_object.parent = level_object
    del light_chunk_data

    for chunk_id, chunk_data in chunks.items():
        print('Unknown level chunk: {:x}'.format(chunk_id))


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
