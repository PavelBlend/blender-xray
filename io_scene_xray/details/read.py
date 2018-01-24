
import bpy
from ..xray_io import PackedReader
from .fmt import DetailsHeader
from .model import imp
from .create import create_pallete, create_images, create_details_slots_object


def read_header(packed_reader):

    fmt_ver, meshes_count, offs_x, offs_z, size_x, size_z = packed_reader.getf('<IIiiII')

    header = DetailsHeader()

    header.format_version = fmt_ver
    header.meshes_count = meshes_count
    header.offset.x = offs_x
    header.offset.y = offs_z
    header.size.x = size_x
    header.size.y = size_z
    header.calc_slots_count()

    return header


def read_details_meshes(base_name, context, chunked_reader, color_indices, header):

    bpy_obj_root = bpy.data.objects.new('{} meshes'.format(base_name), None)
    bpy_obj_root.empty_draw_type = 'SPHERE'
    bpy.context.scene.objects.link(bpy_obj_root)

    step_x = 0.5

    if context.details_models_in_a_row:
        first_offset_x = -step_x * header.meshes_count / 2

    for mesh_id, mesh_data in chunked_reader:
        packed_reader = PackedReader(mesh_data)
        mesh_name = '{0} mesh_{1:0>2}'.format(base_name, mesh_id)

        bpy_obj_mesh = imp.import_(
            mesh_name, context, packed_reader, mode='DETAILS',
            detail_index=mesh_id, detail_colors=color_indices
            )

        bpy_obj_mesh.parent = bpy_obj_root

        if context.details_models_in_a_row:
            bpy_obj_mesh.location[0] = first_offset_x + step_x * mesh_id

    return bpy_obj_root


def read_details_slots(base_name, context, packed_reader, header, color_indices, root_obj):

    create_pallete(color_indices)

    y_coords = []
    y_coords_base = []

    meshes_images_pixels = [
        [1.0 for _ in range(header.slots_count * 4 * 4)] for _ in range(4)
        ]

    from .fmt import PIXELS_OFFSET_1, PIXELS_OFFSET_2

    if header.format_version == 3:

        lights_image_pixels = []
        shadows_image_pixels = []
        hemi_image_pixels = []
        S_IIHHHH = PackedReader.prep('IIHHHH')

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
                meshes_density_data = slot_data[2 : 6]
                for mesh_index, mesh_density in enumerate(meshes_density_data):
                    for corner_index in range(4):

                        corner_density = (
                            (mesh_density >> corner_index * 4) & 0xf) / 0xf

                        pixel_index = \
                            slot_x * 2 + \
                            PIXELS_OFFSET_1[corner_index][0] + \
                            header.size.x * 2 * \
                            (slot_y * 2 + PIXELS_OFFSET_1[corner_index][1])

                        color = color_indices[meshes[mesh_index]]

                        pixels = meshes_images_pixels[mesh_index]
                        pixels[pixel_index * 4] = color[0]    # Red
                        pixels[pixel_index * 4 + 1] = color[1]    # Green
                        pixels[pixel_index * 4 + 2] = color[2]    # Blue
                        pixels[pixel_index * 4 + 3] = corner_density    # Alpha

        create_images(
            header,
            meshes_images_pixels,
            root_obj,
            lights=lights_image_pixels,
            shadows=shadows_image_pixels,
            hemi=hemi_image_pixels
            )

        del meshes_images_pixels
        del lights_image_pixels
        del shadows_image_pixels
        del hemi_image_pixels

    elif header.format_version == 2:

        S_ffBHBHBHBHH = PackedReader.prep('ffBHBHBHBHH')

        lighting_image_pixels = [
            1.0 for _ in range(header.slots_count * 4 * 4)
            ]

        if context.format == 'builds_1233-1558':
            pixels_offset = PIXELS_OFFSET_2

        elif context.format == 'builds_1096-1230':
            pixels_offset = PIXELS_OFFSET_1

        density_pixels_offset = PIXELS_OFFSET_1

        bad_y_base_count = 0
        bad_y_top_count = 0

        for slot_y in range(header.size.y):
            for slot_x in range(header.size.x):
                slot_data = packed_reader.getp(S_ffBHBHBHBHH)

                y_base = slot_data[0]
                y_top = slot_data[1]
                if y_base > 200.0:    # bad y_base coordinate (inf)
                    y_base = 200.0
                    bad_y_base_count += 1
                if y_top < -200.0:    # bad y_top coordinate (-inf)
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
                            (density_data >> corner_index * 4) & 0xf) / 0xf

                        # Red
                        pixels[dens_pixel_index * 4] = color[0]
                        # Green
                        pixels[dens_pixel_index * 4 + 1] = color[1]
                        # Blue
                        pixels[dens_pixel_index * 4 + 2] = color[2]
                        # Alpha
                        pixels[dens_pixel_index * 4 + 3] = corner_density

                        light = (
                            slot_data[10] >> (corner_index * 4) & 0xf) / 0xf

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

        create_images(
            header, meshes_images_pixels, root_obj,
            lights_old=lighting_image_pixels
            )

        del meshes_images_pixels
        del lighting_image_pixels

        if bad_y_base_count > 0:
            context.report({'WARNING'},
                           'details has {} bad base coordinates'.format(
                               bad_y_base_count))

        if bad_y_top_count > 0:
            context.report({'WARNING'},
                           'details has {} bad top coordinates'.format(
                               bad_y_top_count))

    slots_base_object, slots_top_object = create_details_slots_object(
        base_name, header, y_coords, y_coords_base
        )

    del y_coords
    del y_coords_base

    return slots_base_object, slots_top_object
