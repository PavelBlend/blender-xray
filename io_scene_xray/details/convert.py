
from ..utils import AppError
from .fmt import PIXELS_OFFSET_1, DENSITY_DEPTH


def bpy_data_to_lvl_dets_struct(context, bpy_obj):

    from .fmt import LevelDetails
    from .utility import _get_object, _get_image, _validate_object_type

    slots = bpy_obj.xray.detail.slots
    ligthing = slots.ligthing
    meshes = slots.meshes
    lvl_dets = LevelDetails()

    lvl_dets.meshes_object = _get_object(
        bpy_obj, slots.meshes_object, 'Meshes Object'
        )
    _validate_object_type(lvl_dets.meshes_object, 'EMPTY', 'Meshes Object')

    lvl_dets.slots_base_object = _get_object(
        bpy_obj, slots.slots_base_object, 'Slots Base Object'
        )
    _validate_object_type(lvl_dets.slots_base_object, 'MESH', 'Slots Base Object')

    lvl_dets.slots_top_object = _get_object(
        bpy_obj, slots.slots_top_object, 'Slots Top Object'
        )
    _validate_object_type(lvl_dets.slots_top_object, 'MESH', 'Slots Top Object')

    lvl_dets.lights = _get_image(bpy_obj, ligthing.lights_image, 'Lights')

    if context.level_details_format_version == 'builds_1569-cop':
        if ligthing.format != 'builds_1569-cop':
            raise AppError('Object "{0}" has incorrect light format: "Builds 1096-1558". ' \
                'Must be "Builds 1569-CoP"'.format(bpy_obj.name))
        lvl_dets.format_version = 3
        lvl_dets.light_format = '1569-COP'
        lvl_dets.hemi = _get_image(bpy_obj, ligthing.hemi_image, 'Hemi')
        lvl_dets.shadows = _get_image(bpy_obj, ligthing.shadows_image, 'Shadows')
    else:
        if ligthing.format != 'builds_1096-1558':
            raise AppError('Object "{0}" has incorrect light format: "Builds 1569-CoP". ' \
                'Must be "Builds 1096-1558"'.format(bpy_obj.name))
        lvl_dets.format_version = 2
        lvl_dets.light_format = 'OLD'
        if context.level_details_format_version == 'builds_1096-1230':
            lvl_dets.old_format = 1
        elif context.level_details_format_version == 'builds_1233-1558':
            lvl_dets.old_format = 2

    lvl_dets.mesh_0 = _get_image(bpy_obj, meshes.mesh_0, 'Mesh 0')
    lvl_dets.mesh_1 = _get_image(bpy_obj, meshes.mesh_1, 'Mesh 1')
    lvl_dets.mesh_2 = _get_image(bpy_obj, meshes.mesh_2, 'Mesh 2')
    lvl_dets.mesh_3 = _get_image(bpy_obj, meshes.mesh_3, 'Mesh 3')

    return lvl_dets


def bpy_data_to_slots_transforms(lvl_dets):

    base_slots = lvl_dets.slots_base_object
    bbox_base = base_slots.bound_box

    top_slots = lvl_dets.slots_top_object
    bbox_top = top_slots.bound_box

    for bbox_corner_index in range(8):
        for corner_coord_index in range(3):
            if corner_coord_index != 2:    # disregard the z coordinate
                coord_b = int(round(bbox_base[bbox_corner_index][corner_coord_index] / 2.0, 1))
                coord_t = int(round(bbox_top[bbox_corner_index][corner_coord_index] / 2.0, 1))

                if coord_b != coord_t:
                    raise AppError(
                        '"Slots Base Object" size not equal ' \
                        '"Slots Top Object" size'
                        )

    slots_bbox = (
        int(round(bbox_base[0][0] / 2.0, 1)),
        int(round(bbox_base[0][1] / 2.0, 1)),
        int(round(bbox_base[6][0] / 2.0, 1)),
        int(round(bbox_base[6][1] / 2.0, 1))
    )

    lvl_dets.slots_size_x = slots_bbox[2] - slots_bbox[0]
    lvl_dets.slots_size_y = slots_bbox[3] - slots_bbox[1]
    lvl_dets.slots_count = lvl_dets.slots_size_x * lvl_dets.slots_size_y

    if len(base_slots.data.polygons) != lvl_dets.slots_count:
        raise AppError(
            'Slots object "{0}" has an incorrect number of polygons. ' \
            'Must be {1}'.format(base_slots.name, lvl_dets.slots_count)
            )

    if len(top_slots.data.polygons) != lvl_dets.slots_count:
        raise AppError(
            'Slots object "{0}" has an incorrect number of polygons. ' \
            'Must be {1}'.format(top_slots.name, lvl_dets.slots_count)
            )

    lvl_dets.slots_offset_x = -slots_bbox[0]
    lvl_dets.slots_offset_y = -slots_bbox[1]


def _validate_sizes(images, size_x, size_y):
    for image in images:
        if image.size[0] != size_x or image.size[1] != size_y:
            raise AppError('Image "{0}" has incorrect size: {1} x {2}. ' \
                'Must be {3} x {4}.'.format(
                    image.name, image.size[0], image.size[1],
                    size_x, size_y
                    ))


def validate_images_size(lvl_dets):
    if lvl_dets.format_version == 3:
        images_1 = (lvl_dets.lights, lvl_dets.hemi, lvl_dets.shadows)
        images_2 = (lvl_dets.mesh_0, lvl_dets.mesh_1, lvl_dets.mesh_2, lvl_dets.mesh_3)
        _validate_sizes(images_1, lvl_dets.slots_size_x, lvl_dets.slots_size_y)
        _validate_sizes(images_2, lvl_dets.slots_size_x * 2, lvl_dets.slots_size_y * 2)
    elif lvl_dets.format_version == 2:
        images = (
            lvl_dets.lights,
            lvl_dets.mesh_0,
            lvl_dets.mesh_1,
            lvl_dets.mesh_2,
            lvl_dets.mesh_3
            )
        _validate_sizes(images, lvl_dets.slots_size_x * 2, lvl_dets.slots_size_y * 2)


def slot_location_to_slot_index(lvl_dets, slot_location):

    x_slot = int(round(
        (slot_location[0] - 1.0) / lvl_dets.slot_size, 1)) + lvl_dets.slots_offset_x

    y_slot = int(round(
        (slot_location[1] - 1.0) / lvl_dets.slot_size, 1)) + lvl_dets.slots_offset_y

    return y_slot * lvl_dets.slots_size_x + x_slot


def pixel_color_to_density(lvl_dets, pixels, coord_x, coord_y):

    density = []

    for corner_index in range(4):

        pixel_index = (
            (coord_x * 2 + PIXELS_OFFSET_1[corner_index][0] + \
            (coord_y * 2 + PIXELS_OFFSET_1[corner_index][1]) * lvl_dets.slots_size_x * 2) \
            * 4 + 3
            )

        density.append(
            int(round(pixels[pixel_index] / DENSITY_DEPTH, 1)) \
            << (4 * corner_index)
            )

    return density[0] | density[1] | density[2] | density[3]


def pixel_color_to_light(lvl_dets, pixels, coord_x, coord_y, pixels_offset):

    light = []

    for corner_index in range(4):

        pixel_index_r = (
            (coord_x * 2 + pixels_offset[corner_index][0] + \
            (coord_y * 2 + pixels_offset[corner_index][1]) * lvl_dets.slots_size_x * 2) \
            * 4
            )

        pixel_index_g = (
            (coord_x * 2 + pixels_offset[corner_index][0] + \
            (coord_y * 2 + pixels_offset[corner_index][1]) * lvl_dets.slots_size_x * 2) \
            * 4 + 1
            )

        pixel_index_b = (
            (coord_x * 2 + pixels_offset[corner_index][0] + \
            (coord_y * 2 + pixels_offset[corner_index][1]) * lvl_dets.slots_size_x * 2) \
            * 4 + 2
            )

        light.append(
            int(round(((
                pixels[pixel_index_r] + \
                pixels[pixel_index_g] + \
                pixels[pixel_index_b]) / 3) / DENSITY_DEPTH, 1)) \
                << (4 * corner_index))

    return light[0] | light[1] | light[2] | light[3]
