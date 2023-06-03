# standart modules
import os

# blender modules
import bpy
import mathutils

# addon modules
from . import utility
from .. import fmt
from .... import log
from .... import text
from .... import utils


# level collection names
LEVEL_MAIN_COLLECTION_NAME = 'Level'
LEVEL_VISUALS_COLLECTION_NAME = 'Visuals'
LEVEL_CFORM_COLLECTION_NAME = 'CForm'
LEVEL_GLOWS_COLLECTION_NAME = 'Glows'
LEVEL_LIGHTS_COLLECTION_NAME = 'Lights'
LEVEL_PORTALS_COLLECTION_NAME = 'Portals'
LEVEL_SECTORS_COLLECTION_NAME = 'Sectors'

LEVEL_COLLECTION_NAMES = (
    LEVEL_VISUALS_COLLECTION_NAME,
    LEVEL_CFORM_COLLECTION_NAME,
    LEVEL_GLOWS_COLLECTION_NAME,
    LEVEL_LIGHTS_COLLECTION_NAME,
    LEVEL_PORTALS_COLLECTION_NAME,
    LEVEL_SECTORS_COLLECTION_NAME
)

# visuals collection names
LEVEL_VISUALS_NORMAL_COLLECTION_NAME = 'Normal'
LEVEL_VISUALS_HIERRARHY_COLLECTION_NAME = 'Hierrarhy'
LEVEL_VISUALS_PROGRESSIVE_COLLECTION_NAME = 'Progressive'
LEVEL_VISUALS_LOD_COLLECTION_NAME = 'LoD'
LEVEL_VISUALS_TREE_PM_COLLECTION_NAME = 'Tree Progressive'
LEVEL_VISUALS_TREE_ST_COLLECTION_NAME = 'Tree Static'

LEVEL_VISUALS_COLLECTION_NAMES = (
    LEVEL_VISUALS_NORMAL_COLLECTION_NAME,
    LEVEL_VISUALS_HIERRARHY_COLLECTION_NAME,
    LEVEL_VISUALS_PROGRESSIVE_COLLECTION_NAME,
    LEVEL_VISUALS_LOD_COLLECTION_NAME,
    LEVEL_VISUALS_TREE_PM_COLLECTION_NAME,
    LEVEL_VISUALS_TREE_ST_COLLECTION_NAME
)

LEVEL_VISUALS_COLLECTION_NAMES_TABLE = {
    'normal': LEVEL_VISUALS_NORMAL_COLLECTION_NAME,
    'hierrarhy': LEVEL_VISUALS_HIERRARHY_COLLECTION_NAME,
    'progressive': LEVEL_VISUALS_PROGRESSIVE_COLLECTION_NAME,
    'lod': LEVEL_VISUALS_LOD_COLLECTION_NAME,
    'tree_pm': LEVEL_VISUALS_TREE_PM_COLLECTION_NAME,
    'tree_st': LEVEL_VISUALS_TREE_ST_COLLECTION_NAME
}


def create_object(object_name, object_data):
    bpy_object = bpy.data.objects.new(object_name, object_data)
    utils.stats.created_obj()
    return bpy_object


def create_level_object(level, level_collection):
    level_object = create_object(level.name, None)
    level_collection.objects.link(level_object)
    if not utils.version.IS_28:
        utils.version.link_object(level_object)
    level_object.xray.is_level = True
    level_object.xray.level.object_type = 'LEVEL'
    return level_object


def create_sectors_object(level_collection):
    sectors_object = create_object('sectors', None)
    level_collection.objects.link(sectors_object)
    if not utils.version.IS_28:
        utils.version.link_object(sectors_object)
    return sectors_object


def create_level_collections(level):
    if utils.version.IS_28:
        scene_collection = bpy.context.scene.collection
    else:
        scene_collection = None
    # create main collection
    level_collection = utils.version.create_collection(
        level.name, scene_collection
    )
    level.collections[LEVEL_MAIN_COLLECTION_NAME] = level_collection

    # create level collections
    for collection_name in LEVEL_COLLECTION_NAMES:
        collection = utils.version.create_collection(collection_name, level_collection)
        level.collections[collection_name] = collection

    # create visuals collections
    visuals_collection = level.collections[LEVEL_VISUALS_COLLECTION_NAME]
    for collection_name in LEVEL_VISUALS_COLLECTION_NAMES:
        collection = utils.version.create_collection(collection_name, visuals_collection)
        level.collections[collection_name] = collection

    return level_collection


def remove_default_shader_nodes(bpy_material):
    nodes = bpy_material.node_tree.nodes
    for node in nodes:
        nodes.remove(node)


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


def create_empty_image(texture, absolute_image_path):
    bpy_image = bpy.data.images.new(add_extension_to_texture(texture), 0, 0)
    bpy_image.source = 'FILE'
    bpy_image.filepath = absolute_image_path
    bpy_image.alpha_mode = 'STRAIGHT'
    utils.stats.created_img()
    return bpy_image


def load_image(absolute_texture_path):
    if not os.path.exists(absolute_texture_path):
        raise RuntimeError(absolute_texture_path)

    bpy_image = bpy.data.images.load(absolute_texture_path)
    bpy_image.alpha_mode = 'STRAIGHT'
    utils.stats.created_img()

    return bpy_image


def load_image_from_level_folder(context, texture, abs_path):
    level_dir = utility.get_level_dir(context.filepath)
    absolute_texture_path = get_absolute_texture_path(
        level_dir, texture
    )
    try:
        bpy_image = load_image(absolute_texture_path)
    except RuntimeError:    # e.g. 'Error: Cannot read ...'
        absolute_texture_path = get_absolute_texture_path(
            context.textures_folder, texture
        )
        try:
            bpy_image = load_image(absolute_texture_path)
        except RuntimeError:    # e.g. 'Error: Cannot read ...'
            log.warn(text.warn.tex_not_found, path=abs_path)
            bpy_image = create_empty_image(texture, abs_path)
    return bpy_image


def create_image(context, texture, absolute_texture_path):
    try:
        bpy_image = load_image(absolute_texture_path)
    except RuntimeError:    # e.g. 'Error: Cannot read ...'
        bpy_image = load_image_from_level_folder(context, texture, absolute_texture_path)
    bpy_image.use_fake_user = True
    return bpy_image


def search_image(absolute_texture_path):
    for bpy_image in bpy.data.images:
        if is_same_image_paths(bpy_image, absolute_texture_path):
            return bpy_image


def find_image_lmap(context, lmap, level_dir):
    absolute_lmap_path = get_absolute_texture_path(level_dir, lmap)
    bpy_image = search_image(absolute_lmap_path)
    if not bpy_image:
        bpy_image = create_image(context, lmap, absolute_lmap_path)
    bpy_image.colorspace_settings.name = 'Non-Color'
    return bpy_image


def get_image_lmap_terrain(context, lmap):
    level_dir = utility.get_level_dir(context.filepath)
    bpy_image = find_image_lmap(context, lmap, level_dir)
    return bpy_image


def get_image_lmap_brush(context, lmap_1, lmap_2):
    bpy_images = []
    level_dir = utility.get_level_dir(context.filepath)
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
        return (image_lmap, )
    elif light_maps_count == 2:
        image_lmap_1, image_lmap_2 = get_image_lmap_brush(
            context,
            *light_maps
        )
        return (image_lmap_1, image_lmap_2)


def get_image(context, texture, terrain=False):
    if terrain:
        # level dir (terrain texture)
        texture_dir = utility.get_level_dir(context.filepath)
    else:
        texture_dir = context.textures_folder
    absolute_texture_path = get_absolute_texture_path(
        texture_dir,
        texture
    )
    bpy_image = search_image(absolute_texture_path)
    if not bpy_image:
        bpy_image = create_image(context, texture, absolute_texture_path)
    return bpy_image


def is_same_light_maps(context, bpy_material, light_maps):
    has_images = []
    for index, light_map in enumerate(light_maps):
        level_dir = utility.get_level_dir(context.filepath)
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
        context.textures_folder, texture
    )
    level_dir = utility.get_level_dir(context.filepath)
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


def search_material(context, texture, engine_shader, *light_maps):
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


def create_material(level, context, texture, engine_shader, *light_maps):
    bpy_material = bpy.data.materials.new(name=texture)
    bpy_material.xray.version = context.version
    bpy_material.xray.eshader = engine_shader
    bpy_material.xray.uv_texture = 'Texture'
    utils.stats.created_mat()
    if len(light_maps) == 1 and level.xrlc_version >= fmt.VERSION_13:
        bpy_image = get_image(context, texture, terrain=True)
    else:
        bpy_image = get_image(context, texture)
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
        remove_default_shader_nodes(bpy_material)
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


def get_material(level, context, texture, engine_shader, *light_maps):
    bpy_material, bpy_image = search_material(context, texture, engine_shader, *light_maps)
    if not bpy_material:
        bpy_material, bpy_image = create_material(
            level,
            context,
            texture,
            engine_shader,
            *light_maps
        )
    return bpy_material, bpy_image
