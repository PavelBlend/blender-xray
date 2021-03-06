from .. import xray_io
from . import create


def import_brush_shader(context, engine_shader, textures):
    texture, light_map_1, light_map_2 = textures.split(',')
    bpy_material = create.get_material(
        context, texture, engine_shader, light_map_1, light_map_2
    )
    return bpy_material


def import_terrain_shader(context, engine_shader, textures):
    texture, light_map = textures.split(',')
    bpy_material = create.get_material(
        context, texture, engine_shader, light_map
    )
    return bpy_material


def import_vertex_color_shader(context, engine_shader, texture):
    bpy_material = create.get_material(context, texture, engine_shader)
    return bpy_material


def import_shader(context, shader_data):
    engine_shader, textures = shader_data.split('/')
    light_maps_count = textures.count(',')

    if not light_maps_count:
        bpy_material = import_vertex_color_shader(
            context, engine_shader, textures
        )

    elif light_maps_count == 1:
        bpy_material = import_terrain_shader(context, engine_shader, textures)

    elif light_maps_count == 2:
        bpy_material = import_brush_shader(context, engine_shader, textures)

    return bpy_material


def import_first_empty_shader(packed_reader, materials):
    empty_shader_data = packed_reader.gets()
    materials.append(None)


def import_shaders(context, data):
    packed_reader = xray_io.PackedReader(data)
    shaders_count = packed_reader.getf('I')[0]
    materials = []
    import_first_empty_shader(packed_reader, materials)

    for shader_index in range(1, shaders_count):
        shader_data = packed_reader.gets()
        bpy_material = import_shader(context, shader_data)
        materials.append(bpy_material)

    return materials
