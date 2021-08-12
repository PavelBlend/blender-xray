# standart modules
import os

# addon modules
from .. import log
from .. import utils
from .. import version_utils


@log.with_context(name='mesh')
def validate_export_object(context, bpy_obj, fpath):
    log.update(name=bpy_obj.name)
    mesh_name = bpy_obj.data.name

    if not bpy_obj.data.uv_layers:
        raise utils.AppError('mesh "{}" has no UV-map'.format(mesh_name))

    if len(bpy_obj.data.uv_layers) > 1:
        raise utils.AppError('mesh "{}" has more than one UV-map'.format(mesh_name))

    material_count = len(bpy_obj.material_slots)

    if material_count == 0:
        raise utils.AppError('mesh "{}" has no material'.format(mesh_name))

    elif material_count > 1:
        raise utils.AppError('mesh "{}" has more than one material'.format(mesh_name))

    else:
        bpy_material = bpy_obj.material_slots[0].material
        if not bpy_material:
            raise utils.AppError('mesh "{}" has empty material slot'.format(mesh_name))

    bpy_texture = None
    mat_name = bpy_material.name

    if version_utils.IS_28:
        if bpy_material.use_nodes:
            tex_nodes = []
            for node in bpy_material.node_tree.nodes:
                if node.type in version_utils.IMAGE_NODES:
                    tex_nodes.append(node)
            if len(tex_nodes) == 1:
                bpy_texture = tex_nodes[0]
            elif len(tex_nodes) == 0:
                raise utils.AppError('material "{}" has no texture'.format(mat_name))
            else:
                raise utils.AppError(
                    'material "{}" has more than one texture'.format(mat_name)
                )
        else:
            raise utils.AppError('material "{}" does not use nodes'.format(mat_name))
    else:
        for texture_slot in bpy_material.texture_slots:
            if texture_slot:
                bpy_texture = texture_slot.texture
                if bpy_texture:
                    break

    if bpy_texture:

        if bpy_texture.type == 'IMAGE' or bpy_texture.type in version_utils.IMAGE_NODES:
            if context.texname_from_path:
                if bpy_texture.type == 'TEX_ENVIRONMENT':
                    log.warn(
                        'material "{}" has incorrect image node type (Environment Texture)'.format(mat_name),
                        material_name=mat_name,
                        node_name=bpy_texture.name,
                    )
                if bpy_texture.image is None:
                    raise utils.AppError(
                        'material "{}" has no image'.format(mat_name)
                    )
                if not fpath:
                    level_folder = None
                else:
                    level_folder = os.path.dirname(fpath) + os.sep
                texture_name = utils.gen_texture_name(
                    bpy_texture.image, context.textures_folder,
                    level_folder=level_folder
                )
            else:
                texture_name = bpy_texture.name

        else:
            raise utils.AppError(
                'texture "{0}" has an incorrect type: {1}'.format(bpy_texture.name, bpy_texture.type)
                )

    else:
        raise utils.AppError(
            'material "{}" has no texture'.format(mat_name)
        )

    return bpy_material, texture_name
