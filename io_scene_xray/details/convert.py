# addon modules
from . import fmt
from . import utility
from .. import utils
from .. import log
from .. import text


def bpy_data_to_lvl_dets_struct(context, bpy_obj):
    slots = bpy_obj.xray.detail.slots
    ligthing = slots.ligthing
    meshes = slots.meshes
    lvl_dets = fmt.LevelDetails()

    # Meshes object
    lvl_dets.meshes_object = utility.get_object(
        bpy_obj, slots.meshes_object, 'Meshes Object'
    )
    utility.validate_object_type(
        lvl_dets.meshes_object, 'EMPTY', 'Meshes Object'
    )
    # Slots base object
    lvl_dets.slots_base_object = utility.get_object(
        bpy_obj, slots.slots_base_object, 'Slots Base Object'
    )
    utility.validate_object_type(
        lvl_dets.slots_base_object, 'MESH', 'Slots Base Object'
    )
    # Slots top object
    lvl_dets.slots_top_object = utility.get_object(
        bpy_obj, slots.slots_top_object, 'Slots Top Object'
    )
    utility.validate_object_type(
        lvl_dets.slots_top_object, 'MESH', 'Slots Top Object'
    )
    # lights
    lvl_dets.lights = utility.get_image(
        bpy_obj, ligthing.lights_image, 'Lights'
    )

    # Builds 1569-cop
    if context.level_details_format_version == 'builds_1569-cop':
        if ligthing.format != 'builds_1569-cop':
            raise utils.AppError(
                text.error.details_light_1569,
                log.props(object=bpy_obj.name)
            )
        lvl_dets.format_version = fmt.FORMAT_VERSION_3
        lvl_dets.light_format = '1569-COP'
        lvl_dets.hemi = utility.get_image(
            bpy_obj,
            ligthing.hemi_image,
            'Hemi'
        )
        lvl_dets.shadows = utility.get_image(
            bpy_obj, ligthing.shadows_image, 'Shadows'
        )

    # Builds 1096-1558
    else:
        if ligthing.format != 'builds_1096-1558':
            raise utils.AppError(
                text.error.details_light_1096,
                log.props(object=bpy_obj.name)
            )
        lvl_dets.format_version = fmt.FORMAT_VERSION_2
        lvl_dets.light_format = 'OLD'
        if context.level_details_format_version == 'builds_1096-1230':
            lvl_dets.old_format = 1
        else:    # builds 1233-1558'
            lvl_dets.old_format = 2

    # Meshes
    lvl_dets.mesh_0 = utility.get_image(bpy_obj, meshes.mesh_0, 'Mesh 0')
    lvl_dets.mesh_1 = utility.get_image(bpy_obj, meshes.mesh_1, 'Mesh 1')
    lvl_dets.mesh_2 = utility.get_image(bpy_obj, meshes.mesh_2, 'Mesh 2')
    lvl_dets.mesh_3 = utility.get_image(bpy_obj, meshes.mesh_3, 'Mesh 3')

    return lvl_dets


def bpy_data_to_slots_transforms(lvl_dets):
    base_slots = lvl_dets.slots_base_object
    bbox_base = base_slots.bound_box

    top_slots = lvl_dets.slots_top_object
    bbox_top = top_slots.bound_box

    for bbox_corner_index in range(8):
        for corner_coord_index in range(3):
            if corner_coord_index != 2:    # disregard the z coordinate
                coord_b = int(round(
                    bbox_base[bbox_corner_index][corner_coord_index] / 2.0,
                    0
                ))
                coord_t = int(round(
                    bbox_top[bbox_corner_index][corner_coord_index] / 2.0,
                    0
                ))

                if coord_b != coord_t:
                    raise utils.AppError(text.error.details_slots_size)

    slots_bbox = (
        int(round(bbox_base[0][0] / 2.0, 0)),
        int(round(bbox_base[0][1] / 2.0, 0)),
        int(round(bbox_base[6][0] / 2.0, 0)),
        int(round(bbox_base[6][1] / 2.0, 0))
    )

    lvl_dets.slots_size_x = slots_bbox[2] - slots_bbox[0]
    lvl_dets.slots_size_y = slots_bbox[3] - slots_bbox[1]
    lvl_dets.slots_count = lvl_dets.slots_size_x * lvl_dets.slots_size_y

    if len(base_slots.data.polygons) != lvl_dets.slots_count:
        raise utils.AppError(
            text.error.details_poly_count,
            log.props(
                object=base_slots.name,
                must_be=lvl_dets.slots_count,
                size_x=lvl_dets.slots_size_x,
                size_y=lvl_dets.slots_size_y
            )
        )

    if len(top_slots.data.polygons) != lvl_dets.slots_count:
        raise utils.AppError(
            text.error.details_poly_count,
            log.props(
                object=top_slots.name,
                must_be=lvl_dets.slots_count,
                size_x=lvl_dets.slots_size_x,
                size_y=lvl_dets.slots_size_y
            )
        )

    lvl_dets.slots_offset_x = -slots_bbox[0]
    lvl_dets.slots_offset_y = -slots_bbox[1]


def validate_sizes(images, size_x, size_y):
    for image in images:
        if image.size[0] != size_x or image.size[1] != size_y:
            raise utils.AppError(
                text.error.details_img_size,
                log.props(
                    image=image.name,
                    image_size_x=image.size[0],
                    image_size_y=image.size[1],
                    must_be_size_x=size_x,
                    must_be_size_y=size_y
                )
            )


def validate_images_size(lvl_dets):
    if lvl_dets.format_version == fmt.FORMAT_VERSION_3:
        images_1 = (lvl_dets.lights, lvl_dets.hemi, lvl_dets.shadows)
        images_2 = (
            lvl_dets.mesh_0,
            lvl_dets.mesh_1,
            lvl_dets.mesh_2,
            lvl_dets.mesh_3
        )
        validate_sizes(images_1, lvl_dets.slots_size_x, lvl_dets.slots_size_y)
        validate_sizes(
            images_2,
            lvl_dets.slots_size_x * 2,
            lvl_dets.slots_size_y * 2
        )
    else:    # version 2
        images = (
            lvl_dets.lights,
            lvl_dets.mesh_0,
            lvl_dets.mesh_1,
            lvl_dets.mesh_2,
            lvl_dets.mesh_3
        )
        validate_sizes(
            images, lvl_dets.slots_size_x * 2, lvl_dets.slots_size_y * 2
        )


def slot_location_to_slot_index(lvl_dets, slot_location):
    x_slot = int(round(
        (slot_location[0] - 1.0) / lvl_dets.slot_size,
        0
    )) + lvl_dets.slots_offset_x

    y_slot = int(round(
        (slot_location[1] - 1.0) / lvl_dets.slot_size,
        0
    )) + lvl_dets.slots_offset_y

    return y_slot * lvl_dets.slots_size_x + x_slot


def pixel_color_to_density(lvl_dets, pixels, coord_x, coord_y):
    density = []

    for corner_index in range(4):

        pixel_index = (
            (coord_x * 2 + fmt.PIXELS_OFFSET_1[corner_index][0] + \
            (coord_y * 2 + fmt.PIXELS_OFFSET_1[corner_index][1]) * \
            lvl_dets.slots_size_x * 2) * 4 + 3
        )

        density.append(int(round(
            pixels[pixel_index] / fmt.DENSITY_DEPTH,
            0
        )) << (4 * corner_index))

    return density[0] | density[1] | density[2] | density[3]


def pixel_color_to_light(lvl_dets, pixels, coord_x, coord_y, pixels_offset):
    light = []

    for corner_index in range(4):
        indices = []
        for color_component_index in range(3):    # Red, Green, Blue
            pixel_index = (
                (coord_x * 2 + pixels_offset[corner_index][0] + \
                (coord_y * 2 + pixels_offset[corner_index][1]) * \
                lvl_dets.slots_size_x * 2) * 4 + color_component_index
            )
            indices.append(pixel_index)

        average_color = (
            pixels[indices[0]] + pixels[indices[1]] + pixels[indices[2]]
        ) / 3

        light_value = int(round(
            average_color / fmt.DENSITY_DEPTH, 0
        )) << (4 * corner_index)

        light.append(light_value)

    return light[0] | light[1] | light[2] | light[3]
