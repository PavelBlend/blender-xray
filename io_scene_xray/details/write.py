
from ..xray_io import PackedWriter, ChunkedWriter
from ..utils import AppError

from .format import (
    Chunks, FORMAT_VERSION_3, pixels_offset_1, pixels_offset_2,
    DETAIL_MODEL_COUNT_LIMIT
    )


def write_details(cw, ld, cx):

    dm_cw = ChunkedWriter()

    mo = ld.meshes_object
    dm_count = len(mo.children)

    if dm_count == 0:
        raise AppError(
            'Meshes Object "' + mo.name + '" has no children'
            )

    if dm_count > DETAIL_MODEL_COUNT_LIMIT:
        raise AppError(
            'Meshes Object "' + mo.name + '" has too many children: {0}. ' \
            'Not more than {1}.'.format(
                dm_count, DETAIL_MODEL_COUNT_LIMIT
                )
            )

    from .model import exp

    dm_pws = {}
    dm_indices = [0 for _ in range(dm_count)]
    for dm in mo.children:

        if dm.type != 'MESH':
            raise AppError(
                'Meshes Object "' + mo.name + \
                '" has incorrect child object type: {0}. ' \
                'Child object type must be "MESH"'.format(dm.type)
                )

        pw = PackedWriter()
        exp.export(dm, pw, cx, mode='DETAILS')
        dm_index = dm.xray.detail.model.index

        if dm_index >= dm_count:
            raise AppError(
                'Meshes Object "' + dm.name + \
                '" has incorrect "Detail Index": {0}. ' \
                'Must be less than {1}'.format(dm_index, dm_count)
                )

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


def write_header(cw, ld):
    pw = PackedWriter()
    pw.putf('<I', ld.format_version)
    pw.putf('<I', len(ld.meshes_object.children))    # meshes count
    pw.putf('<ii', ld.slots_offset_x, ld.slots_offset_y)
    pw.putf('<II', ld.slots_size_x, ld.slots_size_y)
    cw.put(Chunks.HEADER, pw)


def write_slots_v3(cw, ld):

    from .convert import convert_slot_location_to_slot_index

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

        slot_index_base = convert_slot_location_to_slot_index(
            ld, polygon_base.center
            )

        slot_index_top = convert_slot_location_to_slot_index(
            ld, polygon_top.center
            )

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

    from .utility import generate_meshes_color_indices_table
    from .convert import convert_pixel_color_to_density

    color_indices = generate_meshes_color_indices_table(
        len(ld.meshes_object.children)
        )

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

            density = (
                convert_pixel_color_to_density(ld, meshes_pixels[0], x, y),
                convert_pixel_color_to_density(ld, meshes_pixels[1], x, y),
                convert_pixel_color_to_density(ld, meshes_pixels[2], x, y),
                convert_pixel_color_to_density(ld, meshes_pixels[3], x, y)
                )

            slot = slots[slot_index]

            pw.putf(
                '<II',
                slots[slot_index][0] | slots[slot_index][1] | \
                mesh_0_id << 20 | mesh_1_id << 26, \
                mesh_2_id | mesh_3_id << 6 | \
                shadow << 12 | hemi << 16 | light_r << 20 | light_g << 24 | \
                light_b << 28
                )

            pw.putf('<HHHH', density[0], density[1], density[2], density[3])

            slot_index += 1

    cw.put(Chunks.SLOTS, pw)


def write_slots_v2(cw, ld):

    from .convert import convert_slot_location_to_slot_index
    from .convert import (
        convert_pixel_color_to_density, convert_pixel_color_to_light
        )

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

        slot_index_base = convert_slot_location_to_slot_index(
            ld, polygon_base.center
            )

        slot_index_top = convert_slot_location_to_slot_index(
            ld, polygon_top.center
            )

        slots[slot_index_base][0] = polygon_base.center[2]
        slots[slot_index_top][1] = polygon_top.center[2]

    lights_pixels = list(ld.lights.pixels)

    meshes_pixels = [
        list(ld.mesh_0.pixels),
        list(ld.mesh_1.pixels),
        list(ld.mesh_2.pixels),
        list(ld.mesh_3.pixels)
        ]

    from .utility import generate_meshes_color_indices_table

    color_indices = generate_meshes_color_indices_table(
        len(ld.meshes_object.children), format=2
        )

    slot_index = 0
    color_step = 1.0 / 21

    if ld.old_format == 1:
        pixels_offset = pixels_offset_1
    elif ld.old_format == 2:
        pixels_offset = pixels_offset_2

    for y in range(ld.slots_size_y):
        for x in range(ld.slots_size_x):

            pw.putf('<ff', slots[slot_index][0], slots[slot_index][1])

            slot_index += 1

            for mesh_index in range(4):

                mesh_pixel_index = (x * 2 + ld.slots_size_x * 2 * y * 2) * 4

                mesh_id = color_indices.get((

                    int(round(
                        meshes_pixels[mesh_index][mesh_pixel_index] / color_step, 1)),

                    int(round(
                        meshes_pixels[mesh_index][mesh_pixel_index + 1] / color_step, 1)),

                    int(round(
                        meshes_pixels[mesh_index][mesh_pixel_index + 2] / color_step, 1)),

                    ), 255)

                pw.putf('<B', mesh_id)

                density = convert_pixel_color_to_density(ld, meshes_pixels[mesh_index], x, y)

                pw.putf('<H', density)

            lighting = convert_pixel_color_to_light(
                ld, lights_pixels, x, y, pixels_offset
                )

            pw.putf('<H', lighting)

    cw.put(Chunks.SLOTS, pw)
