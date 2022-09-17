# standart modules
import os

# blender modules
import bpy

# addon modules
from . import image
from . import version
from .. import log
from .. import text


def _is_compatible_texture(texture, file_part):
    tex_folder = version.get_preferences().textures_folder_auto
    tex_path = os.path.join(tex_folder, file_part) + os.extsep + 'dds'
    bpy_image = getattr(texture, 'image', None)
    if bpy_image is None:
        return False, None
    abs_tex_path = os.path.abspath(tex_path)
    abs_image_path = os.path.abspath(bpy_image.filepath)
    if abs_tex_path != abs_image_path:
        return False, None
    return True, bpy_image


def _check_xray_props(material, eshader, cshader, gamemtl, flags):
    if material.xray.flags != flags:
        return False
    if material.xray.eshader != eshader:
        return False
    if material.xray.cshader != cshader:
        return False
    if material.xray.gamemtl != gamemtl:
        return False
    return True


def _check_material_image_28(bpy_material, tex_file_part):
    if bpy_material.use_nodes:
        # collect image texture nodes
        tex_nodes = []
        for node in bpy_material.node_tree.nodes:
            if node.type in version.IMAGE_NODES:
                tex_nodes.append(node)
        # check image node
        if len(tex_nodes) == 1:
            tex_node = tex_nodes[0]
            find_texture, bpy_image = _is_compatible_texture(
                tex_node,
                tex_file_part
            )
            if find_texture:
                return bpy_material, bpy_image
    return None, None


def _check_material_image_27(bpy_material, tex_file_part, uv_map_name):
    tex_slots = []
    # collect texture slots
    for slot in bpy_material.texture_slots:
        if slot:
            if slot.texture:
                tex_slots.append(slot)
    # check texture
    if len(tex_slots) == 1:
        slot = tex_slots[0]
        if slot.uv_layer == uv_map_name:
            find_texture, bpy_image = _is_compatible_texture(
                slot.texture,
                tex_file_part
            )
            if find_texture:
                return bpy_material, bpy_image
    return None, None


def _search_material_and_image(
        name,
        texture,
        eshader,
        cshader,
        gamemtl,
        flags,
        tex_file_part,
        uv_map_name
    ):
    bpy_material = None
    bpy_image = None

    for material in bpy.data.materials:
        # check material name
        correct_name = False
        if material.name == name:
            correct_name = True
        else:
            if material.name.startswith(name):
                if len(material.name) == len(name) + 4:
                    if material.name[-4] == '.':
                        if material.name[-3 : ].isdigit():
                            correct_name = True
        if not correct_name:
            continue

        # check x-ray properties
        is_compatible_xray_props = _check_xray_props(
            material,
            eshader,
            cshader,
            gamemtl,
            flags
        )
        if not is_compatible_xray_props:
            continue

        # check is empty texture
        if not (texture and uv_map_name):
            all_empty_textures = version.is_all_empty_textures(material)
            if all_empty_textures:
                return material, bpy_image

        # check material image
        if version.IS_28:
            bpy_material, bpy_image = _check_material_image_28(
                material,
                tex_file_part
            )
        else:
            bpy_material, bpy_image = _check_material_image_27(
                material,
                tex_file_part,
                uv_map_name
            )

    return bpy_material, bpy_image


def _create_material(name, context, flags, eshader, cshader, gamemtl):
    bpy_material = bpy.data.materials.new(name)
    bpy_material.xray.version = context.version
    bpy_material.xray.flags = flags
    bpy_material.xray.eshader = eshader
    bpy_material.xray.cshader = cshader
    bpy_material.xray.gamemtl = gamemtl
    if version.IS_28:
        bpy_material.use_nodes = True
        bpy_material.blend_method = 'CLIP'
    else:
        bpy_material.use_shadeless = True
        bpy_material.use_transparency = True
        bpy_material.alpha = 0
    return bpy_material


def _create_texture_28(bpy_material, texture, context):
    node_tree = bpy_material.node_tree

    # create texture node
    texture_node = node_tree.nodes.new('ShaderNodeTexImage')
    texture_node.name = texture
    texture_node.label = texture
    texture_node.image = context.image(texture)
    bpy_image = texture_node.image
    texture_node.location.x -= 500.0

    # create node links
    principled_shader = node_tree.nodes['Principled BSDF']
    node_tree.links.new(
        texture_node.outputs['Color'],
        principled_shader.inputs['Base Color']
    )
    node_tree.links.new(
        texture_node.outputs['Alpha'],
        principled_shader.inputs['Alpha']
    )

    return bpy_image


def _create_texture_27(
        bpy_material,
        texture,
        tex_file_part,
        uv_map_name,
        context
    ):

    # search texture
    bpy_texture = bpy.data.textures.get(texture)
    find_texture, bpy_image = _is_compatible_texture(
        bpy_texture,
        tex_file_part
    )

    # create texture
    if not bpy_texture or not find_texture:
        bpy_texture = bpy.data.textures.new(texture, type='IMAGE')
        bpy_texture.image = context.image(texture)
        bpy_texture.use_preview_alpha = True
        bpy_image = bpy_texture.image

    # create texture slot
    bpy_texture_slot = bpy_material.texture_slots.add()
    bpy_texture_slot.texture = bpy_texture
    bpy_texture_slot.texture_coords = 'UV'
    bpy_texture_slot.uv_layer = uv_map_name
    bpy_texture_slot.use_map_color_diffuse = True
    bpy_texture_slot.use_map_alpha = True

    return bpy_image


def _create_material_and_image(
        name,
        context,
        texture,
        flags,
        eshader,
        cshader,
        gamemtl,
        tex_file_part,
        uv_map_name
    ):

    # create material
    bpy_material = _create_material(
        name,
        context,
        flags,
        eshader,
        cshader,
        gamemtl
    )

    # create texture and image
    bpy_image = None
    if texture:
        if version.IS_28:
            bpy_image = _create_texture_28(bpy_material, texture, context)
        else:
            bpy_image = _create_texture_27(
                bpy_material,
                texture,
                tex_file_part,
                uv_map_name,
                context
            )

    return bpy_material, bpy_image


def get_material(
        context,
        name,
        texture,
        eshader,
        cshader,
        gamemtl,
        flags,
        uv_map_name
    ):
    tex_file_part = texture.replace('\\', os.path.sep).lower()

    # search material
    bpy_material, bpy_image = _search_material_and_image(
        name,
        texture,
        eshader,
        cshader,
        gamemtl,
        flags,
        tex_file_part,
        uv_map_name
    )

    # create material
    if bpy_material is None:
        bpy_material, bpy_image = _create_material_and_image(
            name,
            context,
            texture,
            flags,
            eshader,
            cshader,
            gamemtl,
            tex_file_part,
            uv_map_name
        )

    return bpy_material, bpy_image


def _collect_material_textures_28(bpy_material):
    tex_nodes = []
    selected_nodes = []
    active_tex_node = None
    active_node = bpy_material.node_tree.nodes.active
    for node in bpy_material.node_tree.nodes:
        if node.type in version.IMAGE_NODES:
            tex_nodes.append(node)
            if node == active_node:
                active_tex_node = node
            if node.select:
                selected_nodes.append(node)
    return tex_nodes, selected_nodes, active_tex_node


def _find_texture_node_28(
        bpy_material,
        tex_nodes,
        selected_nodes,
        active_tex_node,
        no_err
    ):

    tex_node = None
    name = bpy_material.name

    if not tex_nodes and not no_err:
        raise log.AppError(
            text.error.no_tex,
            log.props(material=name)
        )

    elif len(tex_nodes) == 1:
        tex_node = tex_nodes[0]

    elif len(tex_nodes) > 1:
        for node in bpy_material.node_tree.nodes:
            if node.type == 'OUTPUT_MATERIAL':
                if not node.is_active_output:
                    continue
                links = node.inputs['Surface'].links
                if not links:
                    continue
                shader_node = links[0].from_node
                tex_input = shader_node.inputs.get('Base Color')
                if not tex_input:
                    tex_input = shader_node.inputs.get('Color')
                if not tex_input:
                    continue
                tex_links = tex_input.links
                if not tex_links:
                    continue
                from_node = tex_links[0].from_node
                if from_node.type in version.IMAGE_NODES:
                    tex_node = from_node
                    log.warn(
                        text.warn.use_shader_tex,
                        node_name=tex_node.name,
                        material_name=name
                    )
                    break

        if not tex_node:
            if active_tex_node:
                tex_node = active_tex_node
                log.warn(
                    text.warn.use_active_tex,
                    node_name=tex_node.name,
                    material_name=name
                )
            elif len(selected_nodes) == 1:
                tex_node = selected_nodes[0]
                log.warn(
                    text.warn.use_selected_tex,
                    node_name=tex_node.name,
                    material_name=name
                )
            else:
                raise log.AppError(
                    text.error.mat_many_tex,
                    log.props(material=name)
                )

    return tex_node


def _get_image_relative_path_28(
        context,
        level_folder,
        bpy_material,
        no_err,
        errors
    ):
    tex_name = ''
    if bpy_material.use_nodes:
        (
            tex_nodes,
            selected_nodes,
            active_tex_node
        ) = _collect_material_textures_28(bpy_material)

        tex_node = _find_texture_node_28(
            bpy_material,
            tex_nodes,
            selected_nodes,
            active_tex_node,
            no_err
        )

        if tex_node:
            if tex_node.image:
                if context.texname_from_path:
                    tex_name = image.gen_texture_name(
                        tex_node.image,
                        context.textures_folder,
                        level_folder=level_folder,
                        errors=errors
                    )
                    if tex_node.type == 'TEX_ENVIRONMENT':
                        log.warn(
                            text.warn.env_tex,
                            material_name=bpy_material.name,
                            node_name=tex_node.name,
                        )
                else:
                    tex_name = tex_node.name
        else:
            if not no_err:
                raise log.AppError(
                    text.error.mat_no_img,
                    log.props(material=bpy_material.name)
                )
    else:
        raise log.AppError(
            text.error.mat_not_use_nodes,
            log.props(material=bpy_material.name)
        )
    return tex_name


def _collect_material_textures_27(bpy_material):
    textures = []
    for texture_slot in bpy_material.texture_slots:
        if not texture_slot:
            continue
        texture = texture_slot.texture
        if texture.type != 'IMAGE':
            continue
        if not texture.image:
            continue
        textures.append(texture)
    return textures


def _get_image_relative_path_27(
        context,
        level_folder,
        bpy_material,
        no_err,
        errors
    ):
    texture = None
    tex_name = ''
    textures = _collect_material_textures_27(bpy_material)
    if not len(textures) and not no_err:
        raise log.AppError(
            text.error.no_tex,
            log.props(material=bpy_material.name)
        )
    elif len(textures) == 1:
        texture = textures[0]
    elif len(textures) > 1:
        # use the latest texture as it replaces
        # all previous textures on the stack
        texture = textures[-1]
    if texture:
        if context.texname_from_path:
            tex_name = image.gen_texture_name(
                texture.image,
                context.textures_folder,
                level_folder=level_folder,
                errors=errors
            )
        else:
            tex_name = texture.name
    return tex_name


def get_image_relative_path(
        bpy_material,
        context,
        level_folder=None,
        no_err=True,
        errors=None
    ):
    if version.IS_28:
        tex_name = _get_image_relative_path_28(
            context,
            level_folder,
            bpy_material,
            no_err,
            errors
        )
    else:
        tex_name = _get_image_relative_path_27(
            context,
            level_folder,
            bpy_material,
            no_err,
            errors
        )
    return tex_name
