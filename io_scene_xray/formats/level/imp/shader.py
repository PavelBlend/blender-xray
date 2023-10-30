# addon modules
from . import material
from .. import fmt
from .... import rw


def import_shader(level, context, shader_data):
    engine_shader, textures = shader_data.split('/')
    light_maps_count = textures.count(',')

    # vertex color
    if not light_maps_count:
        lmaps = ()
        texture = textures

    # terrain or single light map
    elif light_maps_count == 1:

        # version 8, 9, 10, 11, 12, 13, 14
        if level.xrlc_version >= fmt.VERSION_8:
            texture, light_map = textures.split(',')

        # version 4, 5
        else:
            light_map, texture = textures.split(',')

        lmaps = (light_map, )

    # light maps
    elif light_maps_count == 2:
        texture, light_map_1, light_map_2 = textures.split(',')
        lmaps = (light_map_1, light_map_2)

    # get material
    bpy_material, bpy_image = material.get_material(
        context,
        texture,
        engine_shader,
        lmaps
    )

    return bpy_material, bpy_image


def import_shaders(level, context, chunks, chunks_ids):
    data = chunks.pop(chunks_ids.SHADERS)
    packed_reader = rw.read.PackedReader(data)
    shaders_count = packed_reader.uint32()

    # version 12, 13, 14
    if level.xrlc_version >= fmt.VERSION_12:
        level.materials = []
        level.images = []

        for _ in range(shaders_count):
            shader = packed_reader.gets()

            if shader:
                bpy_mat, bpy_img = import_shader(level, context, shader)
            else:
                # first empty shader
                bpy_mat = None
                bpy_img = None

            level.materials.append(bpy_mat)
            level.images.append(bpy_img)

    # version 8, 9, 10, 11
    elif fmt.VERSION_8 <= level.xrlc_version <= fmt.VERSION_11:
        level.shaders_or_textures = []
        level.materials = {}
        level.images = {}

        for _ in range(shaders_count):
            shader = packed_reader.gets()
            level.shaders_or_textures.append(shader)

    # version 4, 5
    else:
        level.shaders = []
        level.materials = {}
        level.images = {}

        for _ in range(shaders_count):
            shader = packed_reader.gets()
            level.shaders.append(shader)


def import_textures(level, chunks, chunks_ids):
    if level.xrlc_version >= fmt.VERSION_8:
        return

    data = chunks.pop(chunks_ids.TEXTURES)
    packed_reader = rw.read.PackedReader(data)
    textures_count = packed_reader.uint32()

    level.textures = []

    # version 5
    if level.xrlc_version == fmt.VERSION_5:
        for _ in range(textures_count):
            texture = packed_reader.gets()
            level.textures.append(texture)

    # version 4
    else:
        for _ in range(textures_count):
            texture = packed_reader.gets().split(':', maxsplit=1)[-1]
            level.textures.append(texture)
