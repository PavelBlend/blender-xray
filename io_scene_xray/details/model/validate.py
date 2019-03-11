
from ... import utils


def validate_export_object(context, bpy_obj):

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

    for texture_slot in bpy_material.texture_slots:
        if texture_slot:
            bpy_texture = texture_slot.texture
            if bpy_texture:
                break

    if bpy_texture:

        if bpy_texture.type == 'IMAGE':
            if context.texname_from_path:
                texture_name = utils.gen_texture_name(
                    bpy_texture, context.textures_folder
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
