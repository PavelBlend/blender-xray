# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import log
from .. import text
from .. import utils
from .. import version_utils


def _is_compatible_texture(texture, filepart):
    tex_folder = version_utils.get_preferences().textures_folder_auto
    tex_path = os.path.join(tex_folder, filepart) + os.extsep + 'dds'
    if version_utils.IS_28:
        image = texture.image
        if not image:
            return False
        abs_tex_path = os.path.abspath(tex_path)
        abs_image_path = os.path.abspath(image.filepath)
        if abs_tex_path != abs_image_path:
            return False
        return True
    else:
        image = getattr(texture, 'image', None)
        if image is None:
            return False
        abs_tex_path = os.path.abspath(tex_path)
        abs_image_path = os.path.abspath(image.filepath)
        if abs_tex_path != abs_image_path:
            return False
        return True


def get_material(
        context,
        name,
        texture,
        eshader,
        cshader,
        gamemtl,
        flags,
        vmap
    ):
    bpy_material = None
    tx_filepart = texture.replace('\\', os.path.sep).lower()
    for material in bpy.data.materials:
        if not material.name.startswith(name):
            continue
        if material.xray.flags != flags:
            continue
        if material.xray.eshader != eshader:
            continue
        if material.xray.cshader != cshader:
            continue
        if material.xray.gamemtl != gamemtl:
            continue
        if (not texture) and (not vmap):
            all_empty_textures = version_utils.is_all_empty_textures(material)
            if all_empty_textures:
                bpy_material = material
                break
        if version_utils.IS_28:
            tex_nodes = []
            ts_found = False
            if material.use_nodes:
                for node in material.node_tree.nodes:
                    if not node.type in version_utils.IMAGE_NODES:
                        continue
                    tex_nodes.append(node)
                if len(tex_nodes) != 1:
                    ts_found = False
                else:
                    tex_node = tex_nodes[0]
                    if not _is_compatible_texture(tex_node, tx_filepart):
                        continue
                    ts_found = True
                if not ts_found:
                    continue
                bpy_material = material
                break
        else:
            ts_found = False
            for slot in material.texture_slots:
                if not slot:
                    continue
                if slot.uv_layer != vmap:
                    continue
                if not _is_compatible_texture(slot.texture, tx_filepart):
                    continue
                ts_found = True
                break
            if not ts_found:
                continue
            bpy_material = material
            break
    if bpy_material is None:
        bpy_material = bpy.data.materials.new(name)
        bpy_material.xray.version = context.version
        bpy_material.xray.flags = flags
        bpy_material.xray.eshader = eshader
        bpy_material.xray.cshader = cshader
        bpy_material.xray.gamemtl = gamemtl
        if version_utils.IS_28:
            bpy_material.use_nodes = True
            bpy_material.blend_method = 'CLIP'
        else:
            bpy_material.use_shadeless = True
            bpy_material.use_transparency = True
            bpy_material.alpha = 0
        if texture:
            if version_utils.IS_28:
                node_tree = bpy_material.node_tree
                texture_node = node_tree.nodes.new('ShaderNodeTexImage')
                texture_node.name = texture
                texture_node.label = texture
                texture_node.image = context.image(texture)
                texture_node.location.x -= 500
                princ_shader = node_tree.nodes['Principled BSDF']
                node_tree.links.new(
                    texture_node.outputs['Color'],
                    princ_shader.inputs['Base Color']
                )
                node_tree.links.new(
                    texture_node.outputs['Alpha'],
                    princ_shader.inputs['Alpha']
                )
            else:
                bpy_texture = bpy.data.textures.get(texture)
                if (bpy_texture is None) or \
                        not _is_compatible_texture(bpy_texture, tx_filepart):
                    bpy_texture = bpy.data.textures.new(texture, type='IMAGE')
                    bpy_texture.image = context.image(texture)
                    bpy_texture.use_preview_alpha = True
                bpy_texture_slot = bpy_material.texture_slots.add()
                bpy_texture_slot.texture = bpy_texture
                bpy_texture_slot.texture_coords = 'UV'
                bpy_texture_slot.uv_layer = vmap
                bpy_texture_slot.use_map_color_diffuse = True
                bpy_texture_slot.use_map_alpha = True
    return bpy_material


def get_image_relative_path(material, context, level_folder=None, no_err=True):
    tx_name = ''
    if version_utils.IS_28:
        if material.use_nodes:
            tex_nodes = []
            active_node = material.node_tree.nodes.active
            active_tex_node = None
            tex_node = None
            selected_nodes = []
            for node in material.node_tree.nodes:
                if node.type in version_utils.IMAGE_NODES:
                    tex_nodes.append(node)
                    if node == active_node:
                        active_tex_node = node
                    if node.select:
                        selected_nodes.append(node)
            if not len(tex_nodes) and not no_err:
                raise utils.AppError(
                    text.error.no_tex,
                    log.props(material=material.name)
                )
            elif len(tex_nodes) == 1:
                tex_node = tex_nodes[0]
            elif len(tex_nodes) > 1:
                for node in material.node_tree.nodes:
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
                        if from_node.type in version_utils.IMAGE_NODES:
                            tex_node = from_node
                            break
                if not tex_node:
                    if active_tex_node:
                        tex_node = active_tex_node
                    elif len(selected_nodes) == 1:
                        tex_node = selected_nodes[0]
                    else:
                        raise utils.AppError(
                            text.error.mat_many_tex,
                            log.props(material=material.name)
                        )
            if tex_node:
                if tex_node.image:
                    if context.texname_from_path:
                        tx_name = utils.gen_texture_name(
                            tex_node.image,
                            context.textures_folder,
                            level_folder=level_folder
                        )
                        if tex_node.type == 'TEX_ENVIRONMENT':
                            log.warn(
                                text.warn.env_tex,
                                material_name=material.name,
                                node_name=tex_node.name,
                            )
                    else:
                        tx_name = tex_node.name
            elif not no_err:
                raise utils.AppError(
                    text.error.mat_no_img,
                    log.props(material=material.name)
                )
        else:
            raise utils.AppError(
                text.error.mat_not_use_nodes,
                log.props(material=material.name)
            )
    else:
        textures = []
        for texture_slot in material.texture_slots:
            if not texture_slot:
                continue
            texture = texture_slot.texture
            if texture.type != 'IMAGE':
                continue
            if not texture.image:
                continue
            textures.append(texture)
        texture = None
        if not len(textures) and not no_err:
            raise utils.AppError(
                text.error.no_tex,
                log.props(material=material.name)
            )
        elif len(textures) == 1:
            texture = textures[0]
        elif len(textures) > 1:
            # use the latest texture as it replaces
            # all previous textures on the stack
            texture = textures[-1]
        if texture:
            if context.texname_from_path:
                tx_name = utils.gen_texture_name(
                    texture.image,
                    context.textures_folder,
                    level_folder=level_folder
                )
            else:
                tx_name = texture.name
    return tx_name
