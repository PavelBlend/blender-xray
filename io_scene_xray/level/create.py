import os

import bpy, mathutils

from . import utils


def remove_default_shader_nodes(bpy_material):
    nodes = bpy_material.node_tree.nodes
    for node in nodes:
        nodes.remove(node)


def link_nodes(bpy_material, input_, output):
    links = bpy_material.node_tree.links
    links.new(input_, output)


def create_shader_output_node(bpy_material, offset):
    output_node = bpy_material.node_tree.nodes.new('ShaderNodeOutputMaterial')
    offset.x += 400.0
    output_node.location = offset
    return output_node


def create_shader_principled_node(bpy_material, offset):
    principled_node = bpy_material.node_tree.nodes.new(
        'ShaderNodeBsdfPrincipled'
    )
    offset.x += 400.0
    principled_node.location = offset
    return principled_node


def create_shader_image_node(bpy_material, bpy_image, offset):
    image_node = bpy_material.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.image = bpy_image
    offset.x -= 600.0
    offset.y -= 200.0
    image_node.location = offset
    offset.y += 200.0
    return image_node


def links_nodes(bpy_material, output_node, principled_node, image_node):
    link_nodes(
        bpy_material,
        image_node.outputs['Color'],
        principled_node.inputs['Base Color']
    )
    link_nodes(
        bpy_material,
        image_node.outputs['Alpha'],
        principled_node.inputs['Alpha']
    )
    link_nodes(
        bpy_material,
        principled_node.outputs['BSDF'],
        output_node.inputs['Surface']
    )


def create_shader_nodes(bpy_material, bpy_image):
    offset = mathutils.Vector((0.0, 0.0))
    image_node = create_shader_image_node(bpy_material, bpy_image, offset)
    principled_node = create_shader_principled_node(bpy_material, offset)
    output_node = create_shader_output_node(bpy_material, offset)
    links_nodes(bpy_material, output_node, principled_node, image_node)


def is_same_image_paths(bpy_image, absolute_texture_path):
    absolute_image_path = bpy.path.abspath(bpy_image.filepath)
    is_same_path = absolute_image_path == absolute_texture_path
    return is_same_path


def add_extension_to_texture(texture):
    texture_and_extension = texture + os.extsep + 'dds'
    return texture_and_extension


def get_absolute_texture_path(folder, texture):
    absolute_texture_path = os.path.join(
        folder, add_extension_to_texture(texture)
    )
    return absolute_texture_path


def create_empty_image(texture, absolute_image_path):
    bpy_image = bpy.data.images.new(add_extension_to_texture(texture), 0, 0)
    bpy_image.source = 'FILE'
    bpy_image.filepath = absolute_image_path
    return bpy_image


def load_image(absolute_texture_path):
    bpy_image = bpy.data.images.load(absolute_texture_path)
    return bpy_image


def load_image_from_level_folder(context, texture):
    level_dir = utils.get_level_dir(context.file_path)
    absolute_texture_path = get_absolute_texture_path(
        level_dir, texture
    )
    bpy_image = load_image(absolute_texture_path)
    return bpy_image


def create_image(context, texture, absolute_texture_path):
    try:
        bpy_image = load_image(absolute_texture_path)
    except RuntimeError as ex:  # e.g. 'Error: Cannot read ...'
        try:
            bpy_image = load_image_from_level_folder(context, texture)
        except RuntimeError as ex:  # e.g. 'Error: Cannot read ...'
            context.operator.report({'WARNING'}, str(ex))
            bpy_image = create_empty_image(texture, absolute_texture_path)
    return bpy_image


def search_image(context, texture, absolute_texture_path):
    for bpy_image in bpy.data.images:
        if is_same_image_paths(bpy_image, absolute_texture_path):
            return bpy_image


def get_image(context, texture):
    absolute_texture_path = get_absolute_texture_path(
        context.textures_folder, texture
    )
    bpy_image = search_image(context, texture, absolute_texture_path)
    if not bpy_image:
        bpy_image = create_image(context, texture, absolute_texture_path)
    return bpy_image


def is_same_light_maps(material, light_maps):
    return True


def is_same_image(context, bpy_material, texture):
    absolute_texture_path = get_absolute_texture_path(
        context.textures_folder, texture
    )
    level_dir = utils.get_level_dir(context.file_path)
    absolute_texture_path_in_level_folder = get_absolute_texture_path(
        level_dir, texture
    )
    for node in bpy_material.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            bpy_image = node.image
            if not bpy_image:
                continue
            if not is_same_image_paths(bpy_image, absolute_texture_path):
                if not is_same_image_paths(
                        bpy_image, absolute_texture_path_in_level_folder
                    ):
                    continue
            return bpy_image


def search_material(context, texture, engine_shader, *light_maps):
    for material in bpy.data.materials:
        if not material.name.startswith(texture):
            continue
        if material.xray.eshader != engine_shader:
            continue
        if not is_same_image(context, material, texture):
            continue
        if not is_same_light_maps(material, light_maps):
            continue
        return material


def create_material(context, texture, engine_shader, *light_maps):
    bpy_material = bpy.data.materials.new(name=texture)
    bpy_material.xray.version = context.version
    bpy_material.xray.eshader = engine_shader
    bpy_material.use_nodes = True
    bpy_image = get_image(context, texture)
    remove_default_shader_nodes(bpy_material)
    create_shader_nodes(bpy_material, bpy_image)
    return bpy_material


def get_material(context, texture, engine_shader, *light_maps):
    bpy_material = search_material(context, texture, engine_shader, *light_maps)
    if not bpy_material:
        bpy_material = create_material(
            context, texture, engine_shader, *light_maps
        )
    return bpy_material
