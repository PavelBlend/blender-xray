# blender modules
import bpy
import mathutils

# addon modules
from . import texture
from .. import fmt
from .... import utils


def _create_shader_output_node(bpy_material, offset):
    output_node = bpy_material.node_tree.nodes.new('ShaderNodeOutputMaterial')
    offset.x += 400.0
    output_node.location = offset
    return output_node


def _create_shader_principled_node(bpy_material, offset):
    node = bpy_material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    node.inputs['Specular'].default_value = 0.0
    offset.x += 400.0
    node.location = offset
    return node


def _create_shader_uv_map_node(bpy_material, offset):
    uv_map_node = bpy_material.node_tree.nodes.new('ShaderNodeUVMap')
    uv_map_node.location.x = offset.x
    uv_map_node.location.y = offset.y - 200.0
    uv_map_node.uv_map = 'Texture'
    return uv_map_node


def _create_shader_image_node(bpy_material, bpy_image, offset, rel_tex):
    image_node = bpy_material.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.name = rel_tex
    image_node.label = rel_tex
    image_node.image = bpy_image
    offset.x += 400.0
    image_node.location.x = offset.x
    image_node.location.y = offset.y - 200.0
    return image_node


def _links_nodes(
        bpy_material,
        output_node,
        principled_node,
        image_node,
        uv_map_node,
        lmap_count
    ):

    bpy_material.node_tree.links.new(
        principled_node.outputs['BSDF'],
        output_node.inputs['Surface']
    )
    bpy_material.node_tree.links.new(
        image_node.outputs['Color'],
        principled_node.inputs['Base Color']
    )
    bpy_material.node_tree.links.new(
        uv_map_node.outputs['UV'],
        image_node.inputs['Vector']
    )

    if lmap_count != 1:    # is not terrain
        bpy_material.node_tree.links.new(
            image_node.outputs['Alpha'],
            principled_node.inputs['Alpha']
        )


def _create_shader_nodes(bpy_mat, bpy_img, bpy_img_lmaps, rel_tex):
    # remove default nodes
    bpy_mat.node_tree.nodes.clear()

    offset = mathutils.Vector((-1000.0, 0.0))

    if bpy_img_lmaps:
        lmaps_count = len(bpy_img_lmaps)
    else:
        lmaps_count = 0

    # create nodes
    uv_map_node = _create_shader_uv_map_node(bpy_mat, offset)
    image_node = _create_shader_image_node(bpy_mat, bpy_img, offset, rel_tex)
    principled_node = _create_shader_principled_node(bpy_mat, offset)
    output_node = _create_shader_output_node(bpy_mat, offset)

    # deselect nodes
    for node in bpy_mat.node_tree.nodes:
        node.select = False

    # link nodes
    _links_nodes(
        bpy_mat,
        output_node,
        principled_node,
        image_node,
        uv_map_node,
        lmaps_count
    )


def _search_material(context, rel_tex, engine_shader, light_maps):
    found_mat = None
    found_img = None

    for mat in bpy.data.materials:

        if not mat.name.startswith(rel_tex):
            continue

        if mat.xray.eshader != engine_shader:
            continue

        img = texture.is_same_image(context, mat, rel_tex)

        if not img:
            continue

        if not texture.is_same_light_maps(context, mat, light_maps):
            continue

        found_mat = mat
        found_img = img

        break

    return found_mat, found_img


def _create_material(level, context, rel_tex, engine_shader, light_maps):
    # create material
    bpy_mat = bpy.data.materials.new(name=rel_tex)
    bpy_mat.xray.version = context.version
    bpy_mat.xray.eshader = engine_shader
    bpy_mat.xray.uv_texture = 'Texture'
    utils.stats.created_mat()

    # load images
    bpy_img = context.image(rel_tex)
    bpy_img_lmaps = texture.get_image_lmap(context, light_maps)

    # set light map properties for material
    if bpy_img_lmaps:
        bpy_mat.xray.uv_light_map = 'Light Map'

        for index, lmap_img in enumerate(bpy_img_lmaps):
            setattr(bpy_mat.xray, 'lmap_{}'.format(index), lmap_img.name)

    # set vertex color layers
    else:
        bpy_mat.xray.light_vert_color = 'Light'
        if level.xrlc_version >= fmt.VERSION_11:
            bpy_mat.xray.sun_vert_color = 'Sun'

    if level.xrlc_version >= fmt.VERSION_11:
        bpy_mat.xray.hemi_vert_color = 'Hemi'

    # create shader nodes
    if utils.version.IS_28:

        # set material settings
        bpy_mat.use_nodes = True
        bpy_mat.use_backface_culling = True
        bpy_mat.blend_method = 'CLIP'

        _create_shader_nodes(bpy_mat, bpy_img, bpy_img_lmaps, rel_tex)

    # search or create texture
    else:
        bpy_mat.use_transparency = True
        bpy_mat.alpha = 0.0
        bpy_mat.use_shadeless = True
        bpy_mat.diffuse_intensity = 1.0
        bpy_mat.specular_intensity = 0.0
        tex_slot = bpy_mat.texture_slots.add()

        # find texture
        bpy_texture = None
        for tex in bpy.data.textures:
            if hasattr(tex, 'image'):
                image_path = bpy.path.abspath(tex.image.filepath)
                if texture.is_same_image_paths(bpy_img, image_path):
                    bpy_texture = tex
                    break

        # create texture
        if not bpy_texture:
            bpy_texture = bpy.data.textures.new(rel_tex, 'IMAGE')
            bpy_texture.image = bpy_img
            utils.stats.created_tex()

        tex_slot.texture = bpy_texture
        tex_slot.use_map_alpha = True

    return bpy_mat, bpy_img


def get_material(level, context, rel_tex, eshader, lmaps):
    # search material
    bpy_mat, bpy_img = _search_material(context, rel_tex, eshader, lmaps)

    # create material
    if not bpy_mat:
        bpy_mat, bpy_img = _create_material(
            level,
            context,
            rel_tex,
            eshader,
            lmaps
        )

    return bpy_mat, bpy_img
