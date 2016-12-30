
import io
from .fmt_details import Chunks, FORMAT_VERSION_3
from .xray_io import PackedWriter, ChunkedWriter
from .utils import AppError
from . import fmt_dm_exp


class LevelDetails:
    def __init__(self):
        pass


def _get_image(cx, bpy_obj, xray_prop, prop_name):

    if xray_prop == '':
        raise AppError(
            'object "{0}" has no "{1}"'.format(bpy_obj.name, prop_name)
            )

    bpy_image = cx.bpy.data.images.get(xray_prop)
    if bpy_image == None:
        raise AppError(
            'cannot find "{0}" image: "{1}"'.format(
                prop_name, xray_prop
                )
            )

    return bpy_image


def _get_object(cx, bpy_obj, xray_prop, prop_name):

    if xray_prop == '':
        raise AppError(
            'object "{0}" has no "{1}"'.format(bpy_obj.name, prop_name)
            )

    bpy_object = cx.bpy.data.objects.get(xray_prop)
    if bpy_object == None:
        raise AppError(
            'cannot find "{0}": "{1}"'.format(
                prop_name, xray_prop
                )
            )

    return bpy_object


def _validate_object_type(bpy_obj, type, prop_name):
    if bpy_obj.type != type:
        raise AppError('"{0}" must be of type "{1}"'.format(prop_name, type))


def _get_level_details(cx, bpy_obj):

    x = bpy_obj.xray
    ld = LevelDetails()

    ld.format_version = 3

    ld.meshes_object = _get_object(
        cx, bpy_obj, x.details_meshes_object, 'Meshes Object'
        )
    _validate_object_type(ld.meshes_object, 'EMPTY', 'Meshes Object')

    ld.slots_base_object = _get_object(
        cx, bpy_obj, x.details_slots_base_object, 'Slots Base Object'
        )
    _validate_object_type(ld.slots_base_object, 'MESH', 'Slots Base Object')

    ld.slots_top_object = _get_object(
        cx, bpy_obj, x.details_slots_top_object, 'Slots Top Object'
        )
    _validate_object_type(ld.slots_top_object, 'MESH', 'Slots Top Object')

    if x.details_light_format == 'VERSION_2':
        raise AppError(
            'object "' + bpy_obj.name + '" has not supported lighting format'
            )
    else:
        ld.light_format = '1569-COP'

    ld.lights = _get_image(cx, bpy_obj, x.lights_image, 'Lights')
    ld.hemi = _get_image(cx, bpy_obj, x.hemi_image, 'Hemi')
    ld.shadows = _get_image(cx, bpy_obj, x.shadows_image, 'Shadows')
    ld.mesh_0 = _get_image(cx, bpy_obj, x.slots_mesh_0, 'Mesh 0')
    ld.mesh_1 = _get_image(cx, bpy_obj, x.slots_mesh_1, 'Mesh 1')
    ld.mesh_2 = _get_image(cx, bpy_obj, x.slots_mesh_2, 'Mesh 2')
    ld.mesh_3 = _get_image(cx, bpy_obj, x.slots_mesh_3, 'Mesh 3')

    return ld


def _write_details(cw, ld, cx):

    dm_cw = ChunkedWriter()

    mo = ld.meshes_object
    dm_count = len(mo.children)

    if dm_count == 0:
        raise AppError(
            'Meshes Object "' + mo.name + '" has no childrens'
            )

    if dm_count > 62:
        raise AppError(
            'Meshes Object "' + mo.name + '" has too many childrens: {0}. ' \
            'Must be less than 63.'.format(dm_count)
            )

    dm_pws = {}
    dm_indices = [0 for _ in range(dm_count)]
    for dm in mo.children:
    
        if dm.type != 'MESH':
            raise AppError(
                'Meshes Object "' + mo.name + \
                '" has incorrect children object type: {0}. ' \
                'Children object type must be "MESH"'.format(dm.type)
                )
    
        pw = PackedWriter()
        fmt_dm_exp.export(dm, pw, cx, mode='DETAILS')
        dm_index = dm.xray.detail_index
        dm_indices[dm_index] += 1
        dm_pws[dm_index] = pw

    # validate meshes indices
    for dm_index, count in enumerate(dm_indices):
        if count == 0:

            raise AppError('not detail model with index {0}'.format(
                dm_index
                ))

        elif count > 1:

            raise AppError('duplicated index {0} in detail models'.format(
                dm_index
                ))

    for dm_index in range(dm_count):
        pw = dm_pws[dm_index]
        dm_cw.put(dm_index, pw)

    cw.put(Chunks.MESHES, dm_cw)


def _write_header(cw, ld):
    pw = PackedWriter()
    pw.putf('<I', FORMAT_VERSION_3)
    pw.putf('<I', len(ld.meshes_object.children))    # meshes count
    pw.putf('<ii', ld.slots_offset_x, ld.slots_offset_y)
    pw.putf('<II', ld.slots_size_x, ld.slots_size_y)
    cw.put(Chunks.HEADER, pw)


def _calculate_slots_transforms(ld):

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


def _calc_slot_index_by_location(ld, slot_location):

    x_slot = int(round(
        (slot_location[0] - 1.0) / ld.slot_size, 1)) + ld.slots_offset_x

    y_slot = int(round(
        (slot_location[1] - 1.0) / ld.slot_size, 1)) + ld.slots_offset_y

    return y_slot * ld.slots_size_x + x_slot


def _generate_color_indices():

    mesh_ids = {}
    color_depth = 21
    current_mesh = [color_depth, 0, 0]
    color_channels_reverse = (1, 2, 0)

    mesh_id = 0
    for color_channel in range(3):    # R, G, B
        for _ in range(color_depth):

            mesh_ids[(current_mesh[0], current_mesh[1], current_mesh[2])] = \
                mesh_id

            mesh_id += 1
            current_mesh[color_channel] -= 1
            current_mesh[color_channels_reverse[color_channel]] += 1

    mesh_ids[(0, 0, 0)] = 63    # color index 63 (empty detail mesh)
    color_indices = {}

    for mesh_color, mesh_id in mesh_ids.items():
        color_index = (
            round(mesh_color[0] / color_depth, 2),
            round(mesh_color[1] / color_depth, 2),
            round(mesh_color[2] / color_depth, 2)
            )
        color_indices[color_index] = mesh_id

    return mesh_ids


def _write_slots(cw, ld):
    pw = PackedWriter()
    base_slots_poly = ld.slots_base_object.data.polygons
    top_slots_poly = ld.slots_top_object.data.polygons
    slots = {}
    ld.slot_size = 2.0

    for slot_index in range(ld.slots_count):
        slots[slot_index] = [None, None]

    for slot_index in range(ld.slots_count):
        polygon_base = base_slots_poly[slot_index]
        polygon_top = top_slots_poly[slot_index]
        slot_index_base = _calc_slot_index_by_location(ld, polygon_base.center)
        slot_index_top = _calc_slot_index_by_location(ld, polygon_top.center)
        slots[slot_index_base][0] = int(
            round((polygon_base.center[2] + 200.0) / 0.2, 1)) & 0xfff

        slots[slot_index_top][1] = (
            int(
                round(
                    (polygon_top.center[2] - polygon_base.center[2] - 0.05) \
                    / 0.1, 1
                )
            ) & 0xff) << 12

    lights_pixels = list(ld.lights.pixels)
    hemi_pixels = list(ld.hemi.pixels)
    shadows_pixels = list(ld.shadows.pixels)

    meshes_pixels = [
        list(ld.mesh_0.pixels),
        list(ld.mesh_1.pixels),
        list(ld.mesh_2.pixels),
        list(ld.mesh_3.pixels)
        ]

    color_indices = _generate_color_indices()

    color_step = 1.0 / 21

    slot_index = 0
    for y in range(ld.slots_size_y):
        for x in range(ld.slots_size_x):

            pixel_index = slot_index * 4

            hemi = int(round(0xf * ((
                hemi_pixels[pixel_index] + \
                hemi_pixels[pixel_index + 1] + \
                hemi_pixels[pixel_index + 2]
                ) / 3), 1))

            shadow = int(round(0xf * ((
                shadows_pixels[pixel_index] + \
                shadows_pixels[pixel_index + 1] + \
                shadows_pixels[pixel_index + 2]
                ) / 3), 1))

            light_r = int(round(0xf * (lights_pixels[pixel_index]), 1))
            light_g = int(round(0xf * (lights_pixels[pixel_index + 1]), 1))
            light_b = int(round(0xf * (lights_pixels[pixel_index + 2]), 1))

            mesh_pixel_index = pixel_index * 2 + ld.slots_size_x * y * 2 * 4

            mesh_0_id = color_indices.get((

                int(round(
                    meshes_pixels[0][mesh_pixel_index] / color_step, 1)),

                int(round(
                    meshes_pixels[0][mesh_pixel_index + 1] / color_step, 1)),

                int(round(
                    meshes_pixels[0][mesh_pixel_index + 2] / color_step, 1)),

                ), 63)

            mesh_1_id = color_indices.get((

                int(round(
                    meshes_pixels[1][mesh_pixel_index] / color_step, 1)),

                int(round(
                    meshes_pixels[1][mesh_pixel_index + 1] / color_step, 1)),

                int(round(
                    meshes_pixels[1][mesh_pixel_index + 2] / color_step, 1)),

                ), 63)

            mesh_2_id = color_indices.get((

                int(round(
                    meshes_pixels[2][mesh_pixel_index] / color_step, 1)),

                int(round(
                    meshes_pixels[2][mesh_pixel_index + 1] / color_step, 1)),

                int(round(
                    meshes_pixels[2][mesh_pixel_index + 2] / color_step, 1)),

                ), 63)

            mesh_3_id = color_indices.get((

                int(round(
                    meshes_pixels[3][mesh_pixel_index] / color_step, 1)),

                int(round(
                    meshes_pixels[3][mesh_pixel_index + 1] / color_step, 1)),

                int(round(
                    meshes_pixels[3][mesh_pixel_index + 2] / color_step, 1)),

                ), 63)

            slot = slots[slot_index]
            pw.putf(
                '<II',
                slots[slot_index][0] | slots[slot_index][1] | \
                mesh_0_id << 20 | mesh_1_id << 26, \
                mesh_2_id | mesh_3_id << 6 | \
                shadow << 12 | hemi << 16 | light_r << 20 | light_g << 24 | \
                light_b << 28
                )
            pw.putf('<HHHH', 0xffff, 0xffff, 0xffff, 0xffff)

            slot_index += 1

    cw.put(Chunks.SLOTS, pw)


def _export(bpy_obj, cw, cx):
    ld = _get_level_details(cx, bpy_obj)

    _calculate_slots_transforms(ld)

    _write_details(cw, ld, cx)
    _write_slots(cw, ld)
    _write_header(cw, ld)


def export_file(bpy_obj, fpath, cx):
    with io.open(fpath, 'wb') as f:
        cw = ChunkedWriter()
        _export(bpy_obj, cw, cx)
        f.write(cw.data)
