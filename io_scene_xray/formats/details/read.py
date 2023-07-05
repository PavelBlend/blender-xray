# blender modules
import bpy

# addon modules
from . import create
from . import fmt
from .. import dm
from ... import text
from ... import log
from ... import rw
from ... import utils


def read_header(packed_reader):
    # create header object
    header = fmt.DetailsHeader()

    # read header data
    header.format_version = packed_reader.uint32()

    if header.format_version not in fmt.SUPPORT_FORMAT_VERSIONS:
        raise log.AppError(
            text.error.details_unsupport_ver,
            log.props(version=header.format_version)
        )

    header.meshes_count = packed_reader.uint32()
    header.offset.x, header.offset.y = packed_reader.getf('<2i')
    header.size.x, header.size.y = packed_reader.getf('<2I')

    # calculate slots count
    header.calc_slots_count()

    return header


def read_details_meshes(
        file_path,
        base_name,
        context,
        chunked_reader,
        color_indices,
        header
    ):

    root_name = '{} meshes'.format(base_name)
    bpy_obj_root = bpy.data.objects.new(root_name, None)
    utils.version.set_empty_draw_type(bpy_obj_root, 'SPHERE')
    utils.version.link_object(bpy_obj_root)
    utils.stats.created_obj()

    step_x = 0.5

    if context.models_in_row:
        first_offset_x = -step_x * header.meshes_count / 2

    for mesh_id, mesh_data in chunked_reader:
        packed_reader = rw.read.PackedReader(mesh_data)
        mesh_path = '{0} mesh_{1:0>2}'.format(file_path, mesh_id)

        bpy_obj_mesh = dm.imp.import_(
            mesh_path,
            context,
            packed_reader,
            mode='DETAILS',
            detail_index=mesh_id,
            detail_colors=color_indices
        )

        bpy_obj_mesh.parent = bpy_obj_root

        if context.models_in_row:
            bpy_obj_mesh.location[0] = first_offset_x + step_x * mesh_id

    return bpy_obj_root


@log.with_context('slots')
def read_details_slots(
        base_name,
        context,
        packed_reader,
        header,
        color_indices,
        root_obj
    ):

    create.create_pallete(color_indices)

    y_coords = []
    y_coords_base = []

    meshes_images_pixels = [
        [1.0 for _ in range(header.slots_count * 4 * 4)] for _ in range(4)
    ]

    if header.format_version == fmt.FORMAT_VERSION_3:
        lights_image_pixels = []
        shadows_image_pixels = []
        hemi_image_pixels = []
        S_IIHHHH = rw.read.PackedReader.prep('2I4H')

        for slot_y in range(header.size.y):
            for slot_x in range(header.size.x):

                slot_data = packed_reader.getp(S_IIHHHH)

                # slot Y coordinate
                y_base = slot_data[0] & 0xfff
                y_height = (slot_data[0] >> 12) & 0xff
                y_coord_base = y_base * 0.2 - 200.0
                y_coord = y_coord_base + y_height * 0.1 + 0.05
                y_coords.append(y_coord)
                y_coords_base.append(y_coord_base)

                # meshes indices
                meshes = [
                    (slot_data[0] >> 20) & 0x3f,
                    (slot_data[0] >> 26) & 0x3f,
                    slot_data[1] & 0x3f,
                    (slot_data[1] >> 6) & 0x3f
                ]

                # lighting
                shadow = ((slot_data[1] >> 12) & 0xf) / 0xf
                shadows_image_pixels.extend((shadow, shadow, shadow, 1.0))

                hemi = ((slot_data[1] >> 16) & 0xf) / 0xf
                hemi_image_pixels.extend((hemi, hemi, hemi, 1.0))

                light_r = ((slot_data[1] >> 20) & 0xf) / 0xf
                light_g = ((slot_data[1] >> 24) & 0xf) / 0xf
                light_b = ((slot_data[1] >> 28) & 0xf) / 0xf
                lights_image_pixels.extend((light_r, light_g, light_b, 1.0))

                # meshes density
                density_data = slot_data[2 : 6]
                for mesh_index, density in enumerate(density_data):
                    for corner in range(4):

                        corner_density = ((density >> corner * 4) & 0xf) / 0xf

                        pixel_index = \
                            slot_x * 2 + \
                            fmt.PIXELS_OFFSET_1[corner][0] + \
                            header.size.x * 2 * \
                            (
                                slot_y * 2 + \
                                fmt.PIXELS_OFFSET_1[corner][1]
                            )

                        color = color_indices[meshes[mesh_index]]

                        pixels = meshes_images_pixels[mesh_index]
                        # Red
                        pixels[pixel_index * 4] = color[0]
                        # Green
                        pixels[pixel_index * 4 + 1] = color[1]
                        # Blue
                        pixels[pixel_index * 4 + 2] = color[2]
                        # Alpha
                        pixels[pixel_index * 4 + 3] = corner_density

        create.create_images(
            header,
            meshes_images_pixels,
            root_obj,
            lights=lights_image_pixels,
            shadows=shadows_image_pixels,
            hemi=hemi_image_pixels
        )

    else:    # version 2
        S_ffBHBHBHBHH = rw.read.PackedReader.prep('2fBHBHBHB2H')

        lighting_image_pixels = [
            1.0 for _ in range(header.slots_count * 4 * 4)
        ]

        if context.format_version == 'builds_1233-1558':
            pixels_offset = fmt.PIXELS_OFFSET_2

        else:
            # builds 1096-1230
            pixels_offset = fmt.PIXELS_OFFSET_1

        density_pixels_offset = fmt.PIXELS_OFFSET_1

        bad_y_base_count = 0
        bad_y_top_count = 0

        for slot_y in range(header.size.y):
            for slot_x in range(header.size.x):
                slot_data = packed_reader.getp(S_ffBHBHBHBHH)

                y_base = slot_data[0]
                y_top = slot_data[1]

                # bad y_base coordinate (inf)
                if y_base > 200.0:
                    y_base = 200.0
                    bad_y_base_count += 1

                # bad y_top coordinate (-inf)
                if y_top < -200.0:
                    y_top = -200.0
                    bad_y_top_count += 1

                y_coords.append(y_top)
                y_coords_base.append(y_base)

                data_index = 2

                for mesh_index in range(4):
                    dm_obj_id = slot_data[data_index]
                    if dm_obj_id == 0xff:
                        dm_obj_id = 0x3f

                    density_data = slot_data[data_index + 1]

                    color = color_indices[dm_obj_id]
                    pixels = meshes_images_pixels[mesh_index]

                    for corner_index in range(4):

                        dens_pixel_index = \
                            slot_x * 2 + \
                            density_pixels_offset[corner_index][0] + \
                            header.size.x * 2 * \
                            (slot_y * 2 + \
                            density_pixels_offset[corner_index][1])

                        corner_density = (
                            (density_data >> corner_index * 4) & 0xf
                        ) / 0xf

                        # Red
                        pixels[dens_pixel_index * 4] = color[0]
                        # Green
                        pixels[dens_pixel_index * 4 + 1] = color[1]
                        # Blue
                        pixels[dens_pixel_index * 4 + 2] = color[2]
                        # Alpha
                        pixels[dens_pixel_index * 4 + 3] = corner_density

                        light = (
                            slot_data[10] >> (corner_index * 4) & 0xf
                        ) / 0xf

                        pixel_index = \
                            slot_x * 2 + \
                            pixels_offset[corner_index][0] + \
                            header.size.x * 2 * \
                            (slot_y * 2 + \
                            pixels_offset[corner_index][1])

                        # Red
                        lighting_image_pixels[pixel_index * 4] = light
                        # Green
                        lighting_image_pixels[pixel_index * 4 + 1] = light
                        # Blue
                        lighting_image_pixels[pixel_index * 4 + 2] = light
                        # Alpha
                        lighting_image_pixels[pixel_index * 4 + 3] = 1.0

                    data_index += 2

        create.create_images(
            header,
            meshes_images_pixels,
            root_obj,
            lights_old=lighting_image_pixels
        )

        if bad_y_base_count > 0:
            log.warn(
                text.warn.details_coord_base,
                count=bad_y_base_count
            )

        if bad_y_top_count > 0:
            log.warn(
                text.warn.details_coord_top,
                count=bad_y_top_count
            )

    slots_base_object, slots_top_object = create.create_details_slots_object(
        base_name,
        header,
        y_coords,
        y_coords_base
    )

    return slots_base_object, slots_top_object
