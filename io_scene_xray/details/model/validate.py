import os

from ... import utils
from ...version_utils import IS_28


def validate_export_object(context, bpy_obj, fpath):

    if not bpy_obj.data.uv_layers:
        raise utils.AppError('mesh "' + bpy_obj.data.name + '" has no UV-map')

    material_count = len(bpy_obj.material_slots)

    if material_count == 0:
        raise utils.AppError(
            'mesh "' + bpy_obj.data.name + '" has no material'
        )

    elif material_count > 1:
        raise utils.AppError(
            'mesh "' + bpy_obj.data.name + '" has more than one material'
            )

    else:
        bpy_material = bpy_obj.material_slots[0].material
        if not bpy_material:
            raise utils.AppError(
                'mesh "' + bpy_obj.data.name + '" has empty material slot'
                )

    bpy_texture = None

    if IS_28:
        if bpy_material.use_nodes:
            tex_nodes = []
            for node in bpy_material.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    tex_nodes.append(node)
            if len(tex_nodes) == 1:
                bpy_texture = tex_nodes[0]
            else:
                raise utils.AppError(
                    'material "' + bpy_material.name + '" has more than one texture.'
                )
    else:
        for texture_slot in bpy_material.texture_slots:
            if texture_slot:
                bpy_texture = texture_slot.texture
                if bpy_texture:
                    break

    if bpy_texture:

        if bpy_texture.type == 'IMAGE' or bpy_texture.type == 'TEX_IMAGE':
            if not context.texname_from_path:
                if not fpath:
                    level_folder = None
                else:
                    level_folder = os.path.dirname(fpath) + os.sep
                texture_name = utils.gen_texture_name(
                    bpy_texture, context.textures_folder,
                    level_folder=level_folder
                )
            else:
                texture_name = bpy_texture.name

        else:
            raise utils.AppError(
                'texture "' + bpy_texture.name + \
                '" has an incorrect type: ' + bpy_texture.type
                )

    else:
        raise utils.AppError(
            'material "' + bpy_material.name + '" has no texture'
        )

    return bpy_material, texture_name
