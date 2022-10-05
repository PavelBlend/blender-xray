# standart modules
import os

# addon modules
from ... import log
from ... import text
from ... import utils


@log.with_context(name='export-dm')
def validate_material_and_uv(bpy_obj):
    log.update(object=bpy_obj.name)

    # validate material
    material_count = len(bpy_obj.material_slots)

    if not material_count:
        raise log.AppError(
            text.error.obj_no_mat,
            log.props(object=bpy_obj.name)
        )

    elif material_count > 1:
        raise log.AppError(
            text.error.many_mat,
            log.props(object=bpy_obj.name)
        )

    else:
        bpy_material = bpy_obj.material_slots[0].material

        if not bpy_material:
            raise log.AppError(
                text.error.obj_empty_mat,
                log.props(object=bpy_obj.name)
            )

    # validate uv
    uv_count = len(bpy_obj.data.uv_layers)

    if uv_count != 1:
        if not uv_count:
            raise log.AppError(
                text.error.no_uv,
                log.props(object=bpy_obj.name)
            )

        if uv_count > 1:
            raise log.AppError(
                text.error.dm_many_uv,
                log.props(object=bpy_obj.name)
            )

    return bpy_material


def validate_export_object(context, bpy_obj, file_path, warn_list=None):
    bpy_material = validate_material_and_uv(bpy_obj)

    # generate image relative path
    if not file_path:
        level_folder = None
    else:
        level_folder = os.path.dirname(file_path) + os.sep

    texture_name = utils.material.get_image_relative_path(
        bpy_material,
        context,
        level_folder=level_folder,
        no_err=False,
        errors=warn_list
    )

    return bpy_material, texture_name
