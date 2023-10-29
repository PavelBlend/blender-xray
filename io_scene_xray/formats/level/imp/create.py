# standart modules
import os

# blender modules
import bpy
import mathutils

# addon modules
from .. import fmt
from .... import log
from .... import text
from .... import utils


def link_nodes(bpy_material, input_, output):
    links = bpy_material.node_tree.links
    links.new(input_, output)


def create_shader_output_node(bpy_material, offset):
    output_node = bpy_material.node_tree.nodes.new('ShaderNodeOutputMaterial')
    output_node.select = False
    offset.x += 400.0
    output_node.location = offset
    return output_node


def create_shader_principled_node(bpy_material, offset):
    node = bpy_material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    node.select = False
    node.inputs['Specular'].default_value = 0.0
    offset.x += 400.0
    node.location = offset
    return node


def create_shader_uv_map_texture_node(bpy_material, offset):
    uv_map_node = bpy_material.node_tree.nodes.new('ShaderNodeUVMap')
    offset_y = offset.y - 200.0
    uv_map_node.location = offset.x, offset_y
    uv_map_node.uv_map = 'Texture'
    uv_map_node.select = False
    return uv_map_node


def create_shader_image_node(bpy_material, bpy_image, offset, rel_tex):
    image_node = bpy_material.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.name = rel_tex
    image_node.label = rel_tex
    image_node.select = False
    image_node.image = bpy_image
    offset.x += 400.0
    offset_y = offset.y - 200.0
    image_node.location = offset.x, offset_y
    return image_node


def links_nodes(
        bpy_material,
        output_node,
        principled_node,
        image_node,
        uv_map_node,
        lmap_count
    ):
    link_nodes(
        bpy_material,
        principled_node.outputs['BSDF'],
        output_node.inputs['Surface']
    )
    link_nodes(
        bpy_material,
        image_node.outputs['Color'],
        principled_node.inputs['Base Color']
    )
    link_nodes(
        bpy_material,
        uv_map_node.outputs['UV'],
        image_node.inputs['Vector']
    )
    if lmap_count != 1:    # != terrain
        link_nodes(
            bpy_material,
            image_node.outputs['Alpha'],
            principled_node.inputs['Alpha']
        )


def create_shader_nodes(bpy_material, bpy_image, bpy_image_lmaps, texture):
    # remove default nodes
    bpy_material.node_tree.nodes.clear()

    offset = mathutils.Vector((-1000.0, 0.0))
    uv_map_node = create_shader_uv_map_texture_node(bpy_material, offset)
    image_node = create_shader_image_node(
        bpy_material,
        bpy_image,
        offset,
        texture
    )
    principled_node = create_shader_principled_node(bpy_material, offset)
    output_node = create_shader_output_node(bpy_material, offset)
    if bpy_image_lmaps:
        lmaps_count = len(bpy_image_lmaps)
    else:
        lmaps_count = 0
    links_nodes(
        bpy_material,
        output_node,
        principled_node,
        image_node,
        uv_map_node,
        lmaps_count
    )


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


def get_image_lmap(context, light_maps):
    if not light_maps:
        return None
    light_maps_count = len(light_maps)

    if light_maps_count == 1:
        image_lmap = context.image(light_maps[0])
        image_lmap.colorspace_settings.name = 'Non-Color'
        image_lmap.use_fake_user = True
        return (image_lmap, )

    elif light_maps_count == 2:
        image_lmap_1 = context.image(light_maps[0])
        image_lmap_2 = context.image(light_maps[1])
        image_lmap_1.colorspace_settings.name = 'Non-Color'
        image_lmap_2.colorspace_settings.name = 'Non-Color'
        image_lmap_1.use_fake_user = True
        image_lmap_2.use_fake_user = True
        return (image_lmap_1, image_lmap_2)


def is_same_light_maps(context, bpy_material, light_maps):
    has_images = []
    for index, light_map in enumerate(light_maps):
        level_dir = os.path.dirname(context.filepath)
        absolute_texture_path_in_level_folder = get_absolute_texture_path(
            level_dir, light_map
        )
        image_name = getattr(bpy_material.xray, 'lmap_{}'.format(index))
        bpy_image = bpy.data.images.get(image_name)
        if not bpy_image:
            continue
        if not is_same_image_paths(
                bpy_image,
                absolute_texture_path_in_level_folder
            ):
            continue
        has_images.append(True)
    if len(has_images) == len(light_maps):
        return True


def is_same_image(context, bpy_material, texture):
    absolute_texture_path = get_absolute_texture_path(
        context.tex_folder, texture
    )
    level_dir = os.path.dirname(context.filepath)
    absolute_texture_path_in_level_folder = get_absolute_texture_path(
        level_dir, texture
    )
    if utils.version.IS_28:
        for node in bpy_material.node_tree.nodes:
            if node.type in utils.version.IMAGE_NODES:
                bpy_image = node.image
                if not bpy_image:
                    continue
                if not is_same_image_paths(bpy_image, absolute_texture_path):
                    if not is_same_image_paths(
                            bpy_image,
                            absolute_texture_path_in_level_folder
                        ):
                        continue
                return bpy_image
    else:
        for texture_slot in bpy_material.texture_slots:
            if not texture_slot:
                continue
            if not hasattr(texture_slot.texture, 'image'):
                continue
            bpy_image = texture_slot.texture.image
            if not bpy_image:
                continue
            if not is_same_image_paths(bpy_image, absolute_texture_path):
                if not is_same_image_paths(
                        bpy_image,
                        absolute_texture_path_in_level_folder
                    ):
                    continue
            return bpy_image


def search_material(context, texture, engine_shader, light_maps):
    for material in bpy.data.materials:
        if not material.name.startswith(texture):
            continue
        if material.xray.eshader != engine_shader:
            continue
        image = is_same_image(context, material, texture)
        if not image:
            continue
        if not is_same_light_maps(context, material, light_maps):
            continue
        return material, image
    return None, None


def set_material_settings(bpy_material):
    bpy_material.use_nodes = True
    bpy_material.use_backface_culling = True
    bpy_material.blend_method = 'CLIP'


def create_material(level, context, texture, engine_shader, light_maps):
    bpy_material = bpy.data.materials.new(name=texture)
    bpy_material.xray.version = context.version
    bpy_material.xray.eshader = engine_shader
    bpy_material.xray.uv_texture = 'Texture'
    utils.stats.created_mat()

    bpy_image = context.image(texture)
    bpy_image_lmaps = get_image_lmap(context, light_maps)

    if bpy_image_lmaps:
        bpy_material.xray.uv_light_map = 'Light Map'
        for index, light_map_image in enumerate(bpy_image_lmaps):
            setattr(
                bpy_material.xray,
                'lmap_{}'.format(index),
                light_map_image.name
            )
    else:
        bpy_material.xray.light_vert_color = 'Light'
        bpy_material.xray.sun_vert_color = 'Sun'

    bpy_material.xray.hemi_vert_color = 'Hemi'

    if utils.version.IS_28:
        set_material_settings(bpy_material)
        create_shader_nodes(bpy_material, bpy_image, bpy_image_lmaps, texture)
    else:
        bpy_material.use_transparency = True
        bpy_material.alpha = 0.0
        bpy_material.use_shadeless = True
        bpy_material.diffuse_intensity = 1.0
        bpy_material.specular_intensity = 0.0
        tex_slot = bpy_material.texture_slots.add()
        # find texture
        bpy_texture = None
        for tex in bpy.data.textures:
            if hasattr(tex, 'image'):
                image_path = bpy.path.abspath(tex.image.filepath)
                if is_same_image_paths(bpy_image, image_path):
                    bpy_texture = tex
        if not bpy_texture:
            bpy_texture = bpy.data.textures.new(texture, 'IMAGE')
            bpy_texture.image = bpy_image
            utils.stats.created_tex()
        tex_slot.texture = bpy_texture
        tex_slot.use_map_alpha = True

    return bpy_material, bpy_image


def get_material(level, context, texture, engine_shader, light_maps):
    bpy_material, bpy_image = search_material(context, texture, engine_shader, light_maps)
    if not bpy_material:
        bpy_material, bpy_image = create_material(
            level,
            context,
            texture,
            engine_shader,
            light_maps
        )
    return bpy_material, bpy_image
