# standart modules
import os

# addon modules
from .. import log
from .. import text
from .. import utils
from .. import data_blocks


@log.with_context(name='export-dm')
def validate_export_object(context, bpy_obj, file_path):
    log.update(object=bpy_obj.name)

    if not bpy_obj.data.uv_layers:
        raise log.AppError(
            text.error.no_uv,
            log.props(object=bpy_obj.name)
        )

    if len(bpy_obj.data.uv_layers) > 1:
        raise log.AppError(
            text.error.dm_many_uv,
            log.props(object=bpy_obj.name)
        )

    material_count = len(bpy_obj.material_slots)

    if material_count == 0:
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

    bpy_texture = None
    mat_name = bpy_material.name
    if not file_path:
        level_folder = None
    else:
        level_folder = os.path.dirname(file_path) + os.sep
    texture_name = data_blocks.material.get_image_relative_path(
        bpy_material,
        context,
        level_folder=level_folder,
        no_err=False
    )

    return bpy_material, texture_name
