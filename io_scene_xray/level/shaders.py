# addon modules
from . import create
from . import fmt
from .. import xray_io


def import_brush_shader(level, context, engine_shader, textures):
    texture, light_map_1, light_map_2 = textures.split(',')
    bpy_material, bpy_image = create.get_material(
        level, context, texture, engine_shader, light_map_1, light_map_2
    )
    return bpy_material, bpy_image


def import_brush_shader_v12(level, context, engine_shader, textures):
    texture, light_map = textures.split(',')
    bpy_material, bpy_image = create.get_material(
        level, context, texture, engine_shader, light_map
    )
    return bpy_material, bpy_image


def import_shader_v5(level, context, engine_shader, textures):
    light_map, texture = textures.split(',')
    bpy_material, bpy_image = create.get_material(
        level, context, texture, engine_shader, light_map
    )
    return bpy_material, bpy_image


def import_terrain_shader(level, context, engine_shader, textures):
    texture, light_map = textures.split(',')
    bpy_material, bpy_image = create.get_material(
        level, context, texture, engine_shader, light_map
    )
    return bpy_material, bpy_image


def import_vertex_color_shader(level, context, engine_shader, texture):
    bpy_material, bpy_image = create.get_material(level, context, texture, engine_shader)
    return bpy_material, bpy_image


def import_shader(level, context, shader_data):
    engine_shader, textures = shader_data.split('/')
    light_maps_count = textures.count(',')

    if not light_maps_count:
        bpy_material, bpy_image = import_vertex_color_shader(
            level, context, engine_shader, textures
        )

    elif light_maps_count == 1:
        if level.xrlc_version >= fmt.VERSION_13:
            bpy_material, bpy_image = import_terrain_shader(
                level, context, engine_shader, textures
            )
        elif level.xrlc_version >= fmt.VERSION_8 and level.xrlc_version <= fmt.VERSION_12:
            bpy_material, bpy_image = import_brush_shader_v12(
                level, context, engine_shader, textures
            )
        else:
            bpy_material, bpy_image = import_shader_v5(
                level, context, engine_shader, textures
            )

    elif light_maps_count == 2:
        bpy_material, bpy_image = import_brush_shader(
            level, context, engine_shader, textures
        )

    return bpy_material, bpy_image


def import_first_empty_shader(packed_reader, materials):
    empty_shader_data = packed_reader.gets()
    materials.append(None)


def import_shaders(level, context, data):
    packed_reader = xray_io.PackedReader(data)
    shaders_count = packed_reader.getf('I')[0]

    if level.xrlc_version >= fmt.VERSION_12:
        materials = []
        images = [None, ]    # None - first empty shader
        import_first_empty_shader(packed_reader, materials)
        for shader_index in range(1, shaders_count):
            shader_data = packed_reader.gets()
            bpy_material, bpy_image = import_shader(
                level,
                context,
                shader_data
            )
            materials.append(bpy_material)
            images.append(bpy_image)
    elif fmt.VERSION_8 <= level.xrlc_version <= fmt.VERSION_11:
        level.shaders_or_textures = []
        materials = {}
        images = {}
        for shader_index in range(shaders_count):
            shader_data = packed_reader.gets()
            level.shaders_or_textures.append(shader_data)
    elif level.xrlc_version <= fmt.VERSION_5:
        level.shaders = []
        materials = {}
        images = {}
        for shader_index in range(shaders_count):
            shader_data = packed_reader.gets()
            level.shaders.append(shader_data)

    return materials, images


def import_textures(level, context, data):
    packed_reader = xray_io.PackedReader(data)
    textures_count = packed_reader.getf('I')[0]
    level.textures = []
    if level.xrlc_version > fmt.VERSION_4:
        for texture_index in range(textures_count):
            texture = packed_reader.gets()
            level.textures.append(texture)
    else:
        for texture_index in range(textures_count):
            texture = packed_reader.gets().split(':')[-1]
            level.textures.append(texture)
