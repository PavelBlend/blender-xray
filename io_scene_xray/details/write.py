# addon modules
from . import convert
from . import fmt
from . import utility
from .. import dm
from .. import text
from .. import log
from .. import utils
from .. import xray_io


@log.with_context('mesh')
def write_details(chunked_writer, lvl_dets, context, file_path):
    dm_cw = xray_io.ChunkedWriter()

    meshes_object = lvl_dets.meshes_object
    dm_count = len(meshes_object.children)
    log.update(object=meshes_object.name)

    if not dm_count:
        raise log.AppError(
            text.error.details_no_children,
            log.props(object=meshes_object.name)
        )

    if dm_count > fmt.DETAIL_MODEL_COUNT_LIMIT:
        raise log.AppError(
            text.error.details_many_children,
            log.props(
                object=meshes_object.name,
                children_count=dm_count,
                not_more_than=fmt.DETAIL_MODEL_COUNT_LIMIT
            )
        )

    dm_pws = {}
    dm_indices = [0 for _ in range(dm_count)]
    for detail_model in meshes_object.children:

        if detail_model.type != 'MESH':
            raise log.AppError(
                text.error.details_not_mesh,
                log.props(
                    child_name=detail_model.name,
                    child_type=detail_model.type,
                    meshes_object=meshes_object.name
                )
            )

        packed_writer = xray_io.PackedWriter()
        dm.exp.export(
            detail_model,
            packed_writer,
            context,
            file_path,
            mode='DETAILS'
        )
        dm_index = detail_model.xray.detail.model.index

        if dm_index >= dm_count:
            raise log.AppError(
                text.error.details_bad_detail_index,
                log.props(
                    object=detail_model.name,
                    detail_index=dm_index,
                    must_be_less_than=dm_count
                )
            )

        dm_indices[dm_index] += 1
        dm_pws[dm_index] = packed_writer

    # validate meshes indices
    for dm_index, count in enumerate(dm_indices):
        if not count:
            raise log.AppError(
                text.error.details_no_model_index,
                log.props(index=dm_index)
            )
        elif count > 1:
            raise log.AppError(
                text.error.details_duplicate_model,
                log.props(index=dm_index)
            )

    for dm_index in range(dm_count):
        packed_writer = dm_pws[dm_index]
        dm_cw.put(dm_index, packed_writer)

    chunked_writer.put(fmt.Chunks.MESHES, dm_cw)


def write_header(chunked_writer, lvl_dets):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', lvl_dets.format_version)
    # meshes count
    packed_writer.putf('<I', len(lvl_dets.meshes_object.children))
    packed_writer.putf(
        '<2i',
        lvl_dets.slots_offset_x,
        lvl_dets.slots_offset_y
    )
    packed_writer.putf('<2I', lvl_dets.slots_size_x, lvl_dets.slots_size_y)
    chunked_writer.put(fmt.Chunks.HEADER, packed_writer)


@log.with_context('slots')
def write_slots_v3(chunked_writer, lvl_dets):
    base_obj = lvl_dets.slots_base_object
    top_obj = lvl_dets.slots_top_object
    log.update(objects=(base_obj.name, top_obj.name))
    packed_writer = xray_io.PackedWriter()
    base_slots_poly = base_obj.data.polygons
    top_slots_poly = top_obj.data.polygons
    slots = {}
    lvl_dets.slot_size = 2.0

    for slot_index in range(lvl_dets.slots_count):
        slots[slot_index] = [None, None]

    for slot_index in range(lvl_dets.slots_count):
        polygon_base = base_slots_poly[slot_index]
        polygon_top = top_slots_poly[slot_index]

        slot_index_base = convert.slot_location_to_slot_index(
            lvl_dets, polygon_base.center
        )

        slot_index_top = convert.slot_location_to_slot_index(
            lvl_dets, polygon_top.center
        )

        slots[slot_index_base][0] = int(
            round((polygon_base.center[2] + 200.0) / 0.2, 0)
        ) & 0xfff

        slots[slot_index_top][1] = (int(round(
            (polygon_top.center[2] - polygon_base.center[2] - 0.05) / 0.1,
            0
        )) & 0xff) << 12

    lights_pixels = list(lvl_dets.lights.pixels)
    hemi_pixels = list(lvl_dets.hemi.pixels)
    shadows_pixels = list(lvl_dets.shadows.pixels)

    meshes_pixels = [
        list(lvl_dets.mesh_0.pixels),
        list(lvl_dets.mesh_1.pixels),
        list(lvl_dets.mesh_2.pixels),
        list(lvl_dets.mesh_3.pixels)
    ]

    color_indices = utility.gen_meshes_color_indices_table(
        len(lvl_dets.meshes_object.children)
    )

    color_step = 1.0 / 21

    slot_index = 0
    for coord_y in range(lvl_dets.slots_size_y):
        for coord_x in range(lvl_dets.slots_size_x):
            pixel_index = slot_index * 4

            hemi = int(round(0xf * ((
                hemi_pixels[pixel_index] + \
                hemi_pixels[pixel_index + 1] + \
                hemi_pixels[pixel_index + 2]
            ) / 3), 0))

            shadow = int(round(0xf * ((
                shadows_pixels[pixel_index] + \
                shadows_pixels[pixel_index + 1] + \
                shadows_pixels[pixel_index + 2]
            ) / 3), 0))

            light_r = int(round(0xf * (lights_pixels[pixel_index]), 0))
            light_g = int(round(0xf * (lights_pixels[pixel_index + 1]), 0))
            light_b = int(round(0xf * (lights_pixels[pixel_index + 2]), 0))

            mesh_pixel_index = pixel_index * 2 + lvl_dets.slots_size_x \
                * coord_y * 2 * 4

            mesh_0_id = color_indices.get((

                int(round(
                    meshes_pixels[0][mesh_pixel_index] / color_step, 0)),

                int(round(
                    meshes_pixels[0][mesh_pixel_index + 1] / color_step, 0)),

                int(round(
                    meshes_pixels[0][mesh_pixel_index + 2] / color_step, 0)),

            ), 63)

            mesh_1_id = color_indices.get((

                int(round(
                    meshes_pixels[1][mesh_pixel_index] / color_step, 0)),

                int(round(
                    meshes_pixels[1][mesh_pixel_index + 1] / color_step, 0)),

                int(round(
                    meshes_pixels[1][mesh_pixel_index + 2] / color_step, 0)),

            ), 63)

            mesh_2_id = color_indices.get((

                int(round(
                    meshes_pixels[2][mesh_pixel_index] / color_step, 0)),

                int(round(
                    meshes_pixels[2][mesh_pixel_index + 1] / color_step, 0)),

                int(round(
                    meshes_pixels[2][mesh_pixel_index + 2] / color_step, 0)),

            ), 63)

            mesh_3_id = color_indices.get((

                int(round(
                    meshes_pixels[3][mesh_pixel_index] / color_step, 0)),

                int(round(
                    meshes_pixels[3][mesh_pixel_index + 1] / color_step, 0)),

                int(round(
                    meshes_pixels[3][mesh_pixel_index + 2] / color_step, 0)),

            ), 63)

            density = (
                convert.pixel_color_to_density(
                    lvl_dets, meshes_pixels[0], coord_x, coord_y
                ),
                convert.pixel_color_to_density(
                    lvl_dets, meshes_pixels[1], coord_x, coord_y
                ),
                convert.pixel_color_to_density(
                    lvl_dets, meshes_pixels[2], coord_x, coord_y
                ),
                convert.pixel_color_to_density(
                    lvl_dets, meshes_pixels[3], coord_x, coord_y
                )
            )

            slot = slots[slot_index]

            packed_writer.putf(
                '<2I',
                slot[0] | slot[1] | \
                mesh_0_id << 20 | mesh_1_id << 26, \
                mesh_2_id | mesh_3_id << 6 | \
                shadow << 12 | hemi << 16 | \
                light_r << 20 | light_g << 24 | light_b << 28
            )

            packed_writer.putf(
                '<4H',
                density[0],
                density[1],
                density[2],
                density[3]
            )

            slot_index += 1

    chunked_writer.put(fmt.Chunks.SLOTS, packed_writer)


@log.with_context('slots')
def write_slots_v2(chunked_writer, lvl_dets):
    base_obj = lvl_dets.slots_base_object
    top_obj = lvl_dets.slots_top_object
    log.update(objects=(base_obj.name, top_obj.name))
    packed_writer = xray_io.PackedWriter()
    base_slots_poly = base_obj.data.polygons
    top_slots_poly = top_obj.data.polygons
    slots = {}
    lvl_dets.slot_size = 2.0

    for slot_index in range(lvl_dets.slots_count):
        slots[slot_index] = [None, None]

    for slot_index in range(lvl_dets.slots_count):
        polygon_base = base_slots_poly[slot_index]
        polygon_top = top_slots_poly[slot_index]

        slot_index_base = convert.slot_location_to_slot_index(
            lvl_dets, polygon_base.center
        )

        slot_index_top = convert.slot_location_to_slot_index(
            lvl_dets, polygon_top.center
        )

        slots[slot_index_base][0] = polygon_base.center[2]
        slots[slot_index_top][1] = polygon_top.center[2]

    lights_pixels = list(lvl_dets.lights.pixels)

    meshes_pixels = [
        list(lvl_dets.mesh_0.pixels),
        list(lvl_dets.mesh_1.pixels),
        list(lvl_dets.mesh_2.pixels),
        list(lvl_dets.mesh_3.pixels)
    ]

    color_indices = utility.gen_meshes_color_indices_table(
        len(lvl_dets.meshes_object.children),
        format_version=2
    )

    slot_index = 0
    color_step = 1.0 / 21

    if lvl_dets.old_format == 1:
        pixels_offset = fmt.PIXELS_OFFSET_1
    else:
        pixels_offset = fmt.PIXELS_OFFSET_2

    for coord_y in range(lvl_dets.slots_size_y):
        for coord_x in range(lvl_dets.slots_size_x):
            packed_writer.putf(
                '<2f',
                slots[slot_index][0],
                slots[slot_index][1]
            )

            slot_index += 1

            for mesh_index in range(4):

                mesh_pixel_index = (
                    coord_x * 2 + lvl_dets.slots_size_x * 2 * coord_y * 2
                ) * 4

                mesh_id = color_indices.get((

                    int(round(
                        meshes_pixels[mesh_index][mesh_pixel_index] \
                        / color_step,
                        0
                    )),

                    int(round(
                        meshes_pixels[mesh_index][mesh_pixel_index + 1] \
                        / color_step,
                    0
                    )),

                    int(round(
                        meshes_pixels[mesh_index][mesh_pixel_index + 2] \
                        / color_step,
                        0
                    )),

                ), 255)

                packed_writer.putf('<B', mesh_id)

                density = convert.pixel_color_to_density(
                    lvl_dets,
                    meshes_pixels[mesh_index],
                    coord_x,
                    coord_y
                )

                packed_writer.putf('<H', density)

            lighting = convert.pixel_color_to_light(
                lvl_dets,
                lights_pixels,
                coord_x,
                coord_y,
                pixels_offset
            )

            packed_writer.putf('<H', lighting)

    chunked_writer.put(fmt.Chunks.SLOTS, packed_writer)
