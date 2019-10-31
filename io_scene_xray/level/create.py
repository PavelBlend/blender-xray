import os

import bpy, mathutils

from . import utils


LEVEL_COLLECTION_NAME = 'Level'
LEVEL_VISUALS_COLLECTION_NAME = 'Visuals'
LEVEL_CFORM_COLLECTION_NAME = 'CForm'

# visuals collections
LEVEL_VISUALS_NORMAL_COLLECTION_NAME = 'Normal'
LEVEL_VISUALS_HIERRARHY_COLLECTION_NAME = 'Hierrarhy'
LEVEL_VISUALS_PROGRESSIVE_COLLECTION_NAME = 'Progressive'
LEVEL_VISUALS_LOD_COLLECTION_NAME = 'LoD'
LEVEL_VISUALS_TREE_PM_COLLECTION_NAME = 'Tree Progressive'
LEVEL_VISUALS_TREE_ST_COLLECTION_NAME = 'Tree Static'
LEVEL_VISUALS_FASTPATH_COLLECTION_NAME = 'Fast Path'

LEVEL_VISUALS_COLLECTIONS_NAMES = (
    LEVEL_VISUALS_NORMAL_COLLECTION_NAME,
    LEVEL_VISUALS_HIERRARHY_COLLECTION_NAME,
    LEVEL_VISUALS_PROGRESSIVE_COLLECTION_NAME,
    LEVEL_VISUALS_LOD_COLLECTION_NAME,
    LEVEL_VISUALS_TREE_PM_COLLECTION_NAME,
    LEVEL_VISUALS_TREE_ST_COLLECTION_NAME,
    LEVEL_VISUALS_FASTPATH_COLLECTION_NAME
)

LEVEL_COLLECTIONS_NAMES_TABLE = {
    'normal': LEVEL_VISUALS_NORMAL_COLLECTION_NAME,
    'hierrarhy': LEVEL_VISUALS_HIERRARHY_COLLECTION_NAME,
    'progressive': LEVEL_VISUALS_PROGRESSIVE_COLLECTION_NAME,
    'lod': LEVEL_VISUALS_LOD_COLLECTION_NAME,
    'tree_pm': LEVEL_VISUALS_TREE_PM_COLLECTION_NAME,
    'tree_st': LEVEL_VISUALS_TREE_ST_COLLECTION_NAME,
    'fastpath': LEVEL_VISUALS_FASTPATH_COLLECTION_NAME
}


def create_object(object_name, object_data):
    bpy_object = bpy.data.objects.new(object_name, object_data)
    return bpy_object


def create_level_object(level, level_collection):
    level_object = create_object(level.name, None)
    level_collection.objects.link(level_object)
    level_object.xray.is_level = True
    level_object.xray.level.object_type = 'LEVEL'
    level_object.xray.level.source_path = level.path
    return level_object


def create_sectors_object(level_collection):
    sectors_object = create_object('sectors', None)
    level_collection.objects.link(sectors_object)
    return sectors_object


def create_level_objects(level, level_collection):
    level_object = create_level_object(level, level_collection)
    return level_object


def create_collection(collection_name, parent_collection):
    collection = bpy.data.collections.new(collection_name)
    parent_collection.children.link(collection)
    return collection


def create_level_collections(level):
    level_collection = create_collection(
        level.name, bpy.context.scene.collection
    )
    level.collections[LEVEL_COLLECTION_NAME] = level_collection
    visuals_collection = create_collection(
        LEVEL_VISUALS_COLLECTION_NAME, level_collection
    )
    level.collections[LEVEL_VISUALS_COLLECTION_NAME] = visuals_collection
    cform_collection = create_collection(
        LEVEL_CFORM_COLLECTION_NAME, level_collection
    )
    level.collections[LEVEL_CFORM_COLLECTION_NAME] = cform_collection

    for collection_name in LEVEL_VISUALS_COLLECTIONS_NAMES:
        collection = create_collection(collection_name, visuals_collection)
        level.collections[collection_name] = collection

    return level_collection


def remove_default_shader_nodes(bpy_material):
    nodes = bpy_material.node_tree.nodes
    for node in nodes:
        nodes.remove(node)


def link_nodes(bpy_material, input_, output):
    links = bpy_material.node_tree.links
    links.new(input_, output)


def create_shader_lmaps_nodes(bpy_material, bpy_image_lmaps, offset):
    image_nodes = []
    offset_y = offset.y - 200.0
    for lmap in bpy_image_lmaps:
        if not lmap:
            continue
        image_node = bpy_material.node_tree.nodes.new('ShaderNodeTexImage')
        image_node.select = False
        image_node.image = lmap
        offset_y -= 350.0
        image_node.location = (offset.x, offset_y)
        image_nodes.append(image_node)
    return image_nodes


def create_shader_vertex_colors_nodes(bpy_material, vertex_colors_names, offset):
    vertex_colors_nodes = []
    offset_y = offset.y - 500.0
    for vertex_color_name in vertex_colors_names:
        vertex_colors_node = bpy_material.node_tree.nodes.new('ShaderNodeVertexColor')
        vertex_colors_node.select = False
        vertex_colors_node.layer_name = vertex_color_name
        offset_y -= 200.0
        vertex_colors_node.location = (offset.x, offset_y)
        vertex_colors_nodes.append(vertex_colors_node)
    return vertex_colors_nodes


def create_shader_output_node(bpy_material, offset):
    output_node = bpy_material.node_tree.nodes.new('ShaderNodeOutputMaterial')
    output_node.select = False
    offset.x += 400.0
    output_node.location = offset
    return output_node


def create_shader_principled_node(bpy_material, offset):
    principled_node = bpy_material.node_tree.nodes.new(
        'ShaderNodeBsdfPrincipled'
    )
    principled_node.select = False
    principled_node.inputs['Specular'].default_value = 0.0
    offset.x += 400.0
    principled_node.location = offset
    return principled_node


def create_shader_uv_map_texture_node(
        bpy_material, bpy_image_lmaps, offset
    ):

    uv_map_node = bpy_material.node_tree.nodes.new('ShaderNodeUVMap')
    offset_y = offset.y - 200.0
    uv_map_node.location = offset.x, offset_y
    uv_map_node.uv_map = 'Texture'
    uv_map_node.select = False
    return uv_map_node


def create_shader_uv_map_lmap_node(
        bpy_material, bpy_image_lmaps, offset
    ):

    uv_map_node = bpy_material.node_tree.nodes.new('ShaderNodeUVMap')
    offset_y = offset.y - 600.0
    uv_map_node.location = offset.x, offset_y
    uv_map_node.uv_map = 'Light Map'
    uv_map_node.select = False
    return uv_map_node


def create_shader_uv_map_nodes(
        bpy_material, bpy_image_lmaps, offset
    ):

    uv_map_node = create_shader_uv_map_texture_node(
        bpy_material, bpy_image_lmaps, offset
    )
    if bpy_image_lmaps:
        uv_map_lmap_node = create_shader_uv_map_lmap_node(
            bpy_material, bpy_image_lmaps, offset
        )
    else:
        uv_map_lmap_node = None
    return uv_map_node, uv_map_lmap_node


def create_shader_image_node(bpy_material, bpy_image, offset):
    image_node = bpy_material.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.select = False
    image_node.image = bpy_image
    offset.x += 400.0
    offset_y = offset.y - 200.0
    image_node.location = offset.x, offset_y
    return image_node


def create_shader_mix_rgb_lmap_nodes(bpy_material, offset):
    nodes = []
    # lights + hemi node
    light_hemi_node = bpy_material.node_tree.nodes.new('ShaderNodeMixRGB')
    light_hemi_node.select = False
    offset.x += 400.0
    light_hemi_node.location = offset
    light_hemi_node.label = 'Light + Hemi'
    light_hemi_node.blend_type = 'ADD'
    nodes.append(light_hemi_node)
    light_hemi_node.inputs['Fac'].default_value = 1.0
    # + shadows
    shadows_node = bpy_material.node_tree.nodes.new('ShaderNodeMixRGB')
    shadows_node.select = False
    offset.x += 400.0
    shadows_node.location = offset
    shadows_node.label = '+ Sun'
    shadows_node.blend_type = 'ADD'
    nodes.append(shadows_node)
    shadows_node.inputs['Fac'].default_value = 1.0
    # + ambient
    ambient_node = bpy_material.node_tree.nodes.new('ShaderNodeMixRGB')
    ambient_node.select = False
    offset.x += 400.0
    ambient_node.location = offset
    ambient_node.label = '+ Ambient'
    ambient_node.blend_type = 'ADD'
    ambient_node.inputs['Color2'].default_value = (0.2, 0.2, 0.2, 1.0)
    nodes.append(ambient_node)
    ambient_node.inputs['Fac'].default_value = 1.0
    # + light maps
    light_maps_node = bpy_material.node_tree.nodes.new('ShaderNodeMixRGB')
    light_maps_node.select = False
    offset.x += 400.0
    light_maps_node.location = offset
    light_maps_node.label = '+ Light Maps'
    light_maps_node.blend_type = 'MULTIPLY'
    nodes.append(light_maps_node)
    light_maps_node.inputs['Fac'].default_value = 1.0
    return nodes


def create_shader_mix_rgb_nodes(bpy_material, offset, bpy_image_lmaps):
    nodes = create_shader_mix_rgb_lmap_nodes(bpy_material, offset)
    return nodes


def links_nodes(
        bpy_material, output_node, principled_node, image_node,
        uv_map_nodes, lights_nodes, mix_rgb_nodes
    ):

    link_nodes(
        bpy_material,
        uv_map_nodes[0].outputs['UV'],
        image_node.inputs['Vector']
    )
    if uv_map_nodes[1]:    # light map uv
        for lmap_image_node in lights_nodes:
            link_nodes(
                bpy_material,
                uv_map_nodes[1].outputs['UV'],
                lmap_image_node.inputs['Vector']
            )
        # brush light maps links
        if len(lights_nodes) == 2:
            link_nodes(
                bpy_material,
                lights_nodes[0].outputs['Color'],
                mix_rgb_nodes[0].inputs['Color1']
            )
            link_nodes(
                bpy_material,
                lights_nodes[1].outputs['Color'],
                mix_rgb_nodes[0].inputs['Color2']
            )
            link_nodes(
                bpy_material,
                mix_rgb_nodes[0].outputs['Color'],
                mix_rgb_nodes[1].inputs['Color1']
            )
            link_nodes(
                bpy_material,
                lights_nodes[0].outputs['Alpha'],
                mix_rgb_nodes[1].inputs['Color2']
            )
            link_nodes(
                bpy_material,
                mix_rgb_nodes[1].outputs['Color'],
                mix_rgb_nodes[2].inputs['Color1']
            )
            link_nodes(
                bpy_material,
                image_node.outputs['Color'],
                mix_rgb_nodes[3].inputs['Color1']
            )
            link_nodes(
                bpy_material,
                mix_rgb_nodes[2].outputs['Color'],
                mix_rgb_nodes[3].inputs['Color2']
            )
            link_nodes(
                bpy_material,
                mix_rgb_nodes[3].outputs['Color'],
                principled_node.inputs['Base Color']
            )
        elif len(lights_nodes) == 1:
            # static lights
            link_nodes(
                bpy_material,
                lights_nodes[0].outputs['Color'],
                mix_rgb_nodes[0].inputs['Color1']
            )
            # hemi
            link_nodes(
                bpy_material,
                image_node.outputs['Alpha'],
                mix_rgb_nodes[0].inputs['Color2']
            )
            link_nodes(
                bpy_material,
                mix_rgb_nodes[0].outputs['Color'],
                mix_rgb_nodes[1].inputs['Color1']
            )
            # shadows
            link_nodes(
                bpy_material,
                lights_nodes[0].outputs['Alpha'],
                mix_rgb_nodes[1].inputs['Color2']
            )
            # ambient
            link_nodes(
                bpy_material,
                mix_rgb_nodes[1].outputs['Color'],
                mix_rgb_nodes[2].inputs['Color1']
            )
            # light map + texture
            link_nodes(
                bpy_material,
                image_node.outputs['Color'],
                mix_rgb_nodes[3].inputs['Color1']
            )
            link_nodes(
                bpy_material,
                mix_rgb_nodes[2].outputs['Color'],
                mix_rgb_nodes[3].inputs['Color2']
            )
            link_nodes(
                bpy_material,
                mix_rgb_nodes[3].outputs['Color'],
                principled_node.inputs['Base Color']
            )
    else:    # vertex colors
        link_nodes(
            bpy_material,
            lights_nodes[0].outputs['Color'],
            mix_rgb_nodes[0].inputs['Color1']
        )
        link_nodes(
            bpy_material,
            lights_nodes[1].outputs['Color'],
            mix_rgb_nodes[0].inputs['Color2']
        )
        link_nodes(
            bpy_material,
            mix_rgb_nodes[0].outputs['Color'],
            mix_rgb_nodes[1].inputs['Color1']
        )
        link_nodes(
            bpy_material,
            lights_nodes[2].outputs['Color'],
            mix_rgb_nodes[1].inputs['Color2']
        )
        link_nodes(
            bpy_material,
            mix_rgb_nodes[1].outputs['Color'],
            mix_rgb_nodes[2].inputs['Color1']
        )
        link_nodes(
            bpy_material,
            image_node.outputs['Color'],
            mix_rgb_nodes[3].inputs['Color1']
        )
        link_nodes(
            bpy_material,
            mix_rgb_nodes[2].outputs['Color'],
            mix_rgb_nodes[3].inputs['Color2']
        )
        link_nodes(
            bpy_material,
            mix_rgb_nodes[3].outputs['Color'],
            principled_node.inputs['Base Color']
        )

    if lights_nodes:
        if len(lights_nodes) != 1:    # != terrain
            link_nodes(
                bpy_material,
                image_node.outputs['Alpha'],
                principled_node.inputs['Alpha']
            )
    else:
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


def create_shader_nodes(bpy_material, bpy_image, bpy_image_lmaps):
    offset = mathutils.Vector((-1000.0, 0.0))
    uv_map_nodes = create_shader_uv_map_nodes(
            bpy_material, bpy_image_lmaps, offset
    )
    image_node = create_shader_image_node(bpy_material, bpy_image, offset)
    if bpy_image_lmaps:
        lights_nodes = create_shader_lmaps_nodes(
            bpy_material, bpy_image_lmaps, offset
        )
    else:    # vertex colors
        vertex_colors_names = ('Light', 'Hemi', 'Sun')
        lights_nodes = create_shader_vertex_colors_nodes(
            bpy_material, vertex_colors_names, offset
        )
    mix_rgb_nodes = create_shader_mix_rgb_nodes(
        bpy_material, offset, bpy_image_lmaps
    )
    principled_node = create_shader_principled_node(bpy_material, offset)
    output_node = create_shader_output_node(bpy_material, offset)
    links_nodes(
        bpy_material, output_node, principled_node, image_node,
        uv_map_nodes, lights_nodes, mix_rgb_nodes
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


def find_image_lmap(context, lmap, level_dir):
    absolute_lmap_path = get_absolute_texture_path(
        level_dir, lmap
    )
    bpy_image = search_image(context, lmap, absolute_lmap_path)
    if not bpy_image:
        bpy_image = create_image(context, lmap, absolute_lmap_path)
    bpy_image.colorspace_settings.name = 'Non-Color'
    return bpy_image


def get_image_lmap_terrain(context, lmap):
    level_dir = utils.get_level_dir(context.file_path)
    bpy_image = find_image_lmap(context, lmap, level_dir)
    return bpy_image


def get_image_lmap_brush(context, lmap_1, lmap_2):
    bpy_images = []
    level_dir = utils.get_level_dir(context.file_path)
    for lmap in (lmap_1, lmap_2):
        bpy_image = find_image_lmap(context, lmap, level_dir)
        bpy_images.append(bpy_image)
    return bpy_images[0], bpy_images[1]


def get_image_lmap(context, light_maps):
    if not light_maps:
        return None
    light_maps_count = len(light_maps)
    if light_maps_count == 1:
        image_lmap = get_image_lmap_terrain(context, light_maps[0])
        return image_lmap, None
    elif light_maps_count == 2:
        image_lmap_1, image_lmap_2 = get_image_lmap_brush(context, *light_maps)
        return image_lmap_1, image_lmap_2


def get_image(context, texture, light_maps):
    if len(light_maps) == 1:
        # level dir (terrain texture)
        texture_dir = utils.get_level_dir(context.file_path)
    else:
        texture_dir = context.textures_folder
    absolute_texture_path = get_absolute_texture_path(
        texture_dir, texture
    )
    bpy_image = search_image(context, texture, absolute_texture_path)
    if not bpy_image:
        bpy_image = create_image(context, texture, absolute_texture_path)
    return bpy_image


def is_same_light_maps(context, bpy_material, light_maps):
    has_images = []
    for light_map in light_maps:
        level_dir = utils.get_level_dir(context.file_path)
        absolute_texture_path_in_level_folder = get_absolute_texture_path(
            level_dir, light_map
        )
        has_correct_lmap_image = False
        for node in bpy_material.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                bpy_image = node.image
                if not bpy_image:
                    continue
                if not is_same_image_paths(
                        bpy_image, absolute_texture_path_in_level_folder
                    ):
                    continue
                has_correct_lmap_image = True
        if has_correct_lmap_image:
            has_images.append(has_correct_lmap_image)
    if len(has_images) == len(light_maps):
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
        if not is_same_light_maps(context, material, light_maps):
            continue
        return material


def set_material_settings(bpy_material):
    bpy_material.use_nodes = True
    bpy_material.use_backface_culling = True
    bpy_material.blend_method = 'CLIP'


def create_material(context, texture, engine_shader, *light_maps):
    bpy_material = bpy.data.materials.new(name=texture)
    bpy_material.xray.version = context.version
    bpy_material.xray.eshader = engine_shader
    set_material_settings(bpy_material)
    bpy_image = get_image(context, texture, light_maps)
    bpy_image_lmaps = get_image_lmap(context, light_maps)
    remove_default_shader_nodes(bpy_material)
    create_shader_nodes(bpy_material, bpy_image, bpy_image_lmaps)
    return bpy_material


def get_material(context, texture, engine_shader, *light_maps):
    bpy_material = search_material(context, texture, engine_shader, *light_maps)
    if not bpy_material:
        bpy_material = create_material(
            context, texture, engine_shader, *light_maps
        )
    return bpy_material
