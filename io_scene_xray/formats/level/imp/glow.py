# blender modules
import bpy

# addon modules
from . import create
from .. import fmt
from ... import ogf
from .... import rw
from .... import utils


def _generate_glow_mesh_data(radius):
    verts = []

    for side_index in range(2):    # two sided mesh

        verts.extend((
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

    return verts, faces, uvs


def _create_glow_mesh(name, verts, faces, uvs, material, image):
    # create mesh
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, (), faces)
    utils.stats.created_msh()

    # create uv layer
    if utils.version.IS_28:
        uv_layer = mesh.uv_layers.new(name='Texture')
    else:
        uv_texture = mesh.uv_textures.new(name='Texture')
        uv_layer = mesh.uv_layers[uv_texture.name]
        for tex_poly in uv_texture.data:
            tex_poly.image = image

    # assign uvs
    for uv_index, data in enumerate(uv_layer.data):
        data.uv = uvs[uv_index]

    # append material
    mesh.materials.append(material)

    # change material settings
    if utils.version.IS_28:
        material.use_backface_culling = False
        material.blend_method = 'BLEND'

    return mesh


def _create_glow_object(glow_id, pos, radius, material, image):
    obj_name = 'glow_{:0>3}'.format(glow_id)

    # get geometry
    verts, faces, uvs = _generate_glow_mesh_data(radius)

    # create mesh
    mesh = _create_glow_mesh(obj_name, verts, faces, uvs, material, image)

    # create object
    glow_object = create.create_object(obj_name, mesh)
    glow_object.xray.isroot = False
    glow_object.location = pos

    return glow_object


def _create_glow_object_v12(level, glow_id, pos, radius, shader_id):
    # get material and image
    material = level.materials[shader_id]
    image = level.images[shader_id]

    # create glow-object
    glow_object = _create_glow_object(glow_id, pos, radius, material, image)

    return glow_object


def _create_glow_object_v5(level, glow_id, pos, radius, shader_id, tex_id):
    # get material and image
    material = ogf.imp.material.get_level_material(level, shader_id, tex_id)
    image = level.images[tex_id]

    # create glow-object
    glow_object = _create_glow_object(glow_id, pos, radius, material, image)

    return glow_object


def _import_glow_v12(level, packed_reader, glow_index):
    # read
    position = packed_reader.getv3f()
    radius = packed_reader.getf('<f')[0]
    shader_index = packed_reader.getf('<H')[0]

    # create
    glow_object = _create_glow_object_v12(
        level,
        glow_index,
        position,
        radius,
        shader_index
    )

    return glow_object


def _import_glow_v5(level, packed_reader, glow_index):
    # read
    position = packed_reader.getv3f()
    radius = packed_reader.getf('<f')[0]
    texture_index = packed_reader.uint32()
    shader_index = packed_reader.uint32()

    # create
    glow_object = _create_glow_object_v5(
        level,
        glow_index,
        position,
        radius,
        shader_index,
        texture_index
    )

    return glow_object


def _create_glows_object(collection, level_object):
    glows_object = create.create_object('glows', None)
    glows_object.parent = level_object
    collection.objects.link(glows_object)
    level_object.xray.level.glows_obj = glows_object.name

    if not utils.version.IS_28:
        utils.version.link_object(glows_object)

    return glows_object


def _link_glow_object(glow_object, glows_object, level, collection):
    glow_object.parent = glows_object
    glow_object.xray.version = level.addon_version
    collection.objects.link(glow_object)

    if not utils.version.IS_28:
        utils.version.link_object(glow_object)


def _import_glows_v12(data, level, level_object):
    packed_reader = rw.read.PackedReader(data)

    # create glows root-object
    collection = level.collections[create.LEVEL_GLOWS_COLLECTION_NAME]
    glows_object = _create_glows_object(collection, level_object)

    glows_count = len(data) // fmt.GLOW_SIZE_V12

    for glow_index in range(glows_count):

        # create glow-object
        glow_object = _import_glow_v12(level, packed_reader, glow_index)

        _link_glow_object(glow_object, glows_object, level, collection)


def _import_glows_v5(data, level, level_object):
    packed_reader = rw.read.PackedReader(data)

    # create glows root-object
    collection = level.collections[create.LEVEL_GLOWS_COLLECTION_NAME]
    glows_object = _create_glows_object(collection, level_object)

    glows_count = len(data) // fmt.GLOW_SIZE_V5

    for glow_index in range(glows_count):

        # create glow-object
        glow_object = _import_glow_v5(level, packed_reader, glow_index)

        _link_glow_object(glow_object, glows_object, level, collection)


def import_glows(level, level_object, chunks, chunks_ids):
    glows_data = chunks.pop(chunks_ids.GLOWS)

    if level.xrlc_version >= fmt.VERSION_12:
        _import_glows_v12(glows_data, level, level_object)
    else:
        _import_glows_v5(glows_data, level, level_object)
