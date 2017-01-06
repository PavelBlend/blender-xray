
from io_scene_xray.utils import AppError
from .format import pixels_offset_1, density_depth


def convert_bpy_data_to_level_details_struct(cx, bpy_obj):

    from .format import LevelDetails
    from .utility import _get_object, _get_image, _validate_object_type

    s = bpy_obj.xray.detail.slots
    l = s.ligthing
    m = s.meshes
    ld = LevelDetails()

    if cx.level_details_format_version == 'NEW':
        ld.format_version = 3
    else:
        ld.format_version = 2
        if cx.level_details_format_version == 'OLD_1':
            ld.old_format = 1
        elif cx.level_details_format_version == 'OLD_2':
            ld.old_format = 2

    ld.meshes_object = _get_object(
        cx, bpy_obj, s.meshes_object, 'Meshes Object'
        )
    _validate_object_type(ld.meshes_object, 'EMPTY', 'Meshes Object')

    ld.slots_base_object = _get_object(
        cx, bpy_obj, s.slots_base_object, 'Slots Base Object'
        )
    _validate_object_type(ld.slots_base_object, 'MESH', 'Slots Base Object')

    ld.slots_top_object = _get_object(
        cx, bpy_obj, s.slots_top_object, 'Slots Top Object'
        )
    _validate_object_type(ld.slots_top_object, 'MESH', 'Slots Top Object')

    ld.lights = _get_image(cx, bpy_obj, l.lights_image, 'Lights')

    if l.format == 'VERSION_2':

        if cx.level_details_format_version == 'NEW':
            raise AppError(
                'Object "{0}" has incorrect light format: "Old". ' \
                'Must be "New".'.format(bpy_obj.name))

        ld.light_format = 'OLD'

    else:
        ld.light_format = '1569-COP'

        ld.hemi = _get_image(cx, bpy_obj, l.hemi_image, 'Hemi')
        ld.shadows = _get_image(cx, bpy_obj, l.shadows_image, 'Shadows')

    ld.mesh_0 = _get_image(cx, bpy_obj, m.mesh_0, 'Mesh 0')
    ld.mesh_1 = _get_image(cx, bpy_obj, m.mesh_1, 'Mesh 1')
    ld.mesh_2 = _get_image(cx, bpy_obj, m.mesh_2, 'Mesh 2')
    ld.mesh_3 = _get_image(cx, bpy_obj, m.mesh_3, 'Mesh 3')

    return ld


def convert_bpy_data_to_slots_transforms(ld):

    base_slots = ld.slots_base_object
    bbox_base = base_slots.bound_box

    top_slots = ld.slots_top_object
    bbox_top = top_slots.bound_box

    for i in range(8):
        for ii in range(3):
            if ii != 2:
                coord_b = int(round(bbox_base[i][ii] / 2.0, 1))
                coord_t = int(round(bbox_top[i][ii] / 2.0, 1))

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

    ld.slots_size_x = slots_bbox[2] - slots_bbox[0]
    ld.slots_size_y = slots_bbox[3] - slots_bbox[1]
    ld.slots_count = ld.slots_size_x * ld.slots_size_y

    if len(base_slots.data.polygons) != ld.slots_count:
        raise AppError(
            'Slots object "{0}" has an incorrect number of polygons. ' \
            'Must be {1}'.format(base_slots.name, ld.slots_count)
            )

    if len(top_slots.data.polygons) != ld.slots_count:
        raise AppError(
            'Slots object "{0}" has an incorrect number of polygons. ' \
            'Must be {1}'.format(top_slots.name, ld.slots_count)
            )

    ld.slots_offset_x = -slots_bbox[0]
    ld.slots_offset_y = -slots_bbox[1]


def convert_slot_location_to_slot_index(ld, slot_location):

    x_slot = int(round(
        (slot_location[0] - 1.0) / ld.slot_size, 1)) + ld.slots_offset_x

    y_slot = int(round(
        (slot_location[1] - 1.0) / ld.slot_size, 1)) + ld.slots_offset_y

    return y_slot * ld.slots_size_x + x_slot


def convert_pixel_color_to_density(ld, pixels, x, y):

    density = []

    for corner_index in range(4):

        pixel_index = (
            (x * 2 + pixels_offset_1[corner_index][0] + \
            (y * 2 + pixels_offset_1[corner_index][1]) * ld.slots_size_x * 2) \
            * 4 + 3
            )

        density.append(
            int(round(pixels[pixel_index] / density_depth, 1)) \
            << (4 * corner_index)
            )

    return density[0] | density[1] | density[2] | density[3]


def convert_pixel_color_to_light(ld, pixels, x, y, pixels_offset):

    light = []

    for corner_index in range(4):

        pixel_index_r = (
            (x * 2 + pixels_offset[corner_index][0] + \
            (y * 2 + pixels_offset[corner_index][1]) * ld.slots_size_x * 2) \
            * 4
            )

        pixel_index_g = (
            (x * 2 + pixels_offset[corner_index][0] + \
            (y * 2 + pixels_offset[corner_index][1]) * ld.slots_size_x * 2) \
            * 4 + 1
            )

        pixel_index_b = (
            (x * 2 + pixels_offset[corner_index][0] + \
            (y * 2 + pixels_offset[corner_index][1]) * ld.slots_size_x * 2) \
            * 4 + 2
            )

        light.append(
            int(round(((
                pixels[pixel_index_r] + \
                pixels[pixel_index_g] + \
                pixels[pixel_index_b]) / 3) / density_depth, 1)) \
                << (4 * corner_index))

    return light[0] | light[1] | light[2] | light[3]
