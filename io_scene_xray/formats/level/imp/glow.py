# blender modules
import bpy

# addon modules
from . import create
from .. import fmt
from ... import ogf
from .... import rw
from .... import utils


def _generate_glow_mesh_data(radius):
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


def _create_glow_mesh(name, vertices, faces, uvs, material, image):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, (), faces)
    utils.stats.created_msh()
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


def _create_glow_object(
        glow_index,
        position,
        radius,
        shader_index,
        materials,
        images
    ):
    object_name = 'glow_{:0>3}'.format(glow_index)
    vertices, faces, uvs = _generate_glow_mesh_data(radius)
    material = materials[shader_index]
    image = images[shader_index]
    mesh = _create_glow_mesh(
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


def _create_glow_object_v5(
        level,
        glow_index,
        position,
        radius,
        shader_index,
        texture_index
    ):
    object_name = 'glow_{:0>3}'.format(glow_index)
    vertices, faces, uvs = _generate_glow_mesh_data(radius)
    material = ogf.imp.material.get_level_material(
        level,
        shader_index,
        texture_index
    )
    image = level.images[texture_index]
    mesh = _create_glow_mesh(
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


def _import_glow(packed_reader, glow_index, materials, images):
    position = packed_reader.getf('<3f')
    radius = packed_reader.getf('<f')[0]
    shader_index = packed_reader.getf('<H')[0]
    glow_object = _create_glow_object(
        glow_index,
        position,
        radius,
        shader_index,
        materials,
        images
    )
    return glow_object


def _import_glow_v5(level, packed_reader, glow_index):
    position = packed_reader.getf('<3f')
    radius = packed_reader.getf('<f')[0]
    texture_index = packed_reader.uint32()
    shader_index = packed_reader.uint32()
    glow_object = _create_glow_object_v5(
        level, glow_index, position, radius,
        shader_index, texture_index
    )
    return glow_object


def _create_glows_object(collection):
    object_name = 'glows'
    bpy_object = create.create_object(object_name, None)
    collection.objects.link(bpy_object)
    if not utils.version.IS_28:
        utils.version.link_object(bpy_object)
    return bpy_object


def import_glows_v12(data, level, level_object):
    packed_reader = rw.read.PackedReader(data)
    glows_count = len(data) // fmt.GLOW_SIZE
    collection = level.collections[create.LEVEL_GLOWS_COLLECTION_NAME]
    glows_object = _create_glows_object(collection)
    glows_object.parent = level_object
    level_object.xray.level.glows_obj = glows_object.name
    materials = level.materials
    images = level.images

    for glow_index in range(glows_count):
        glow_object = _import_glow(
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


def import_glows_v5(data, level, level_object):
    packed_reader = rw.read.PackedReader(data)
    glows_count = len(data) // fmt.GLOW_SIZE_V5
    collection = level.collections[create.LEVEL_GLOWS_COLLECTION_NAME]
    glows_object = _create_glows_object(collection)
    glows_object.parent = level_object
    level_object.xray.level.glows_obj = glows_object.name

    for glow_index in range(glows_count):
        glow_object = _import_glow_v5(level, packed_reader, glow_index)
        glow_object.parent = glows_object
        glow_object.xray.version = level.addon_version
        glow_object.xray.isroot = False
        collection.objects.link(glow_object)
        if not utils.version.IS_28:
            utils.version.link_object(glow_object)
