# blender modules
import bpy

# addon modules
from ... import utils
from ... import log
from ... import text


def get_image(bpy_obj, xray_prop, prop_name):
    if xray_prop == '':
        raise log.AppError(
            text.error.details_has_no_img,
            log.props(image=prop_name, object=bpy_obj.name)
        )

    bpy_image = bpy.data.images.get(xray_prop)
    if bpy_image is None:
        raise log.AppError(
            text.error.details_cannot_find_img,
            log.props(image=xray_prop, prop=prop_name)
        )

    return bpy_image


def get_object(bpy_obj, xray_prop, prop_name):
    if xray_prop == '':
        raise log.AppError(
            text.error.details_has_no_obj,
            log.props(prop=prop_name, object=bpy_obj.name)
        )

    bpy_object = bpy.data.objects.get(xray_prop)
    if bpy_object is None:
        raise log.AppError(
            text.error.details_cannot_find_obj,
            log.props(prop=prop_name, object=xray_prop)
        )

    return bpy_object


def validate_object_type(bpy_obj, obj_type, prop_name):
    if bpy_obj.type != obj_type:
        raise log.AppError(
            text.error.details_wrong_type,
            log.props(
                prop=prop_name,
                object=bpy_obj.name,
                object_type=bpy_obj.type,
                object_type_must_be=obj_type
            )
        )


def gen_meshes_color_indices_table(detail_models_count, format_version=3):
    mesh_ids = {}
    color_depth = 21
    current_mesh = [color_depth, 0, 0]
    color_channels_reverse = (1, 2, 0)
    append_last_mesh_color = False

    mesh_id = 0
    for color_channel in range(3):    # R, G, B
        for _ in range(color_depth):
            mesh_ids[(
                current_mesh[0],
                current_mesh[1],
                current_mesh[2]
            )] = mesh_id

            mesh_id += 1
            current_mesh[color_channel] -= 1
            current_mesh[color_channels_reverse[color_channel]] += 1

            if mesh_id >= detail_models_count:
                append_last_mesh_color = True
                break

        if append_last_mesh_color:
            break

    if format_version == 3:
        mesh_ids[(0, 0, 0)] = 63    # empty detail mesh (version 3)
    else:
        mesh_ids[(0, 0, 0)] = 255    # empty detail mesh (version 2)

    return mesh_ids


def generate_color_indices():
    mesh_ids = []
    color_depth = 21
    current_mesh = [color_depth, 0, 0]
    color_channels_reverse = (1, 2, 0)

    for color_channel in range(3):    # R, G, B
        for _ in range(color_depth):
            mesh_ids.append((
                current_mesh[0],
                current_mesh[1],
                current_mesh[2]
            ))
            current_mesh[color_channel] -= 1
            current_mesh[color_channels_reverse[color_channel]] += 1

    mesh_ids.append([0, 0, 0])    # color index 63 (empty detail mesh)
    color_indices = []

    for mesh_id in mesh_ids:
        color_index = (
            mesh_id[0] / color_depth,
            mesh_id[1] / color_depth,
            mesh_id[2] / color_depth,
            1.0
        )
        color_indices.append(color_index)

    return color_indices
