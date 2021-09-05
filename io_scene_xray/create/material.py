# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import version_utils


def _is_compatible_texture(texture, filepart):
    tex_folder = version_utils.get_preferences().textures_folder_auto
    tex_path = os.path.join(tex_folder, filepart) + os.extsep + 'dds'
    if version_utils.IS_28:
        image = texture.image
        if not image:
            return False
        if tex_path != image.filepath:
            return False
        return True
    else:
        image = getattr(texture, 'image', None)
        if image is None:
            return False
        if tex_path != image.filepath:
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
