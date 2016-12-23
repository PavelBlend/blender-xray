
import os
import io
from . import fmt_dm_imp
from .fmt_details import Chunks, SUPPORT_FORMAT_VERSIONS
from .utils import AppError
from .xray_io import ChunkedReader, PackedReader


class DetailsHeader:

    class Transform:
        def __init__(self):
            self.x = None
            self.y = None

    def __init__(self):
        self.format_version = None
        self.slot_size = 2.0
        self.slot_half = self.slot_size / 2
        self.meshes_count = None
        self.offset = self.Transform()
        self.size = self.Transform()
        self.slots_count = 0

    def calc_slots_count(self):
        self.slots_count = self.size.x * self.size.y


def _read_header(pr):

    fmt_ver, meshes_count, offs_x, offs_z, size_x, size_z = pr.getf('<IIiiII')

    header = DetailsHeader()

    header.format_version = fmt_ver
    header.meshes_count = meshes_count
    header.offset.x = offs_x
    header.offset.y = offs_z
    header.size.x = size_x
    header.size.y = size_z
    header.calc_slots_count()

    return header


def _read_details_meshes(base_name, cx, cr, color_indices, header):

    bpy_obj_root = cx.bpy.data.objects.new('{} meshes'.format(base_name), None)
    cx.bpy.context.scene.objects.link(bpy_obj_root)

    step_x = 0.5

    if cx.details_models_in_a_row:
        first_offset_x = -step_x * header.meshes_count / 2

    for mesh_id, mesh_data in cr:
        pr = PackedReader(mesh_data)
        mesh_name = '{0} mesh_{1:0>2}'.format(base_name, mesh_id)

        bpy_obj_mesh = fmt_dm_imp.import_(
            mesh_name, cx, pr, mode='DETAILS',
            detail_index=mesh_id, detail_colors=color_indices
            )

        bpy_obj_mesh.parent = bpy_obj_root

        if cx.details_models_in_a_row:
            bpy_obj_mesh.location[0] = first_offset_x + step_x * mesh_id

    return bpy_obj_root


def _create_details_slots_object(
        base_name, cx, header, y_coords_top, y_coords_base
        ):

    slots_name_base = '{0} slots base'.format(base_name)
    slots_base_mesh = cx.bpy.data.meshes.new(slots_name_base)
    slots_base_object = cx.bpy.data.objects.new(
        slots_name_base, slots_base_mesh
        )
    cx.bpy.context.scene.objects.link(slots_base_object)

    slots_name_top = '{0} slots top'.format(base_name)
    slots_top_mesh = cx.bpy.data.meshes.new(slots_name_top)
    slots_top_object = cx.bpy.data.objects.new(
        slots_name_top, slots_top_mesh
        )
    cx.bpy.context.scene.objects.link(slots_top_object)

    slots_base = []
    slots_top = []
    uvs = []
    uv_face_size_x = 1.0 / header.size.x
    uv_face_size_y = 1.0 / header.size.y
    slot_id = 0

    for coord_y in range(header.size.y):
        for coord_x in range(header.size.x):

            # append UV's
            uv_x = coord_x * uv_face_size_x
            uv_x_plus = uv_x + uv_face_size_x
            uv_y = coord_y * uv_face_size_y
            uv_y_plus = uv_y + uv_face_size_y
            uvs.extend((
                        (uv_x, uv_y),
                        (uv_x_plus, uv_y),
                        (uv_x_plus, uv_y_plus),
                        (uv_x, uv_y_plus)
                      ))

            slot_x_coord = (coord_x - header.offset.x) * header.slot_size + \
                               header.slot_half

            slot_z_coord = (coord_y - header.offset.y) * header.slot_size + \
                               header.slot_half

            slots_base.append((
                slot_x_coord, slot_z_coord, y_coords_base[slot_id]
                ))

            slots_top.append((
                slot_x_coord, slot_z_coord, y_coords_top[slot_id]
                ))

            slot_id += 1

    def _offset_vert_coord(vert_coord_x, vert_coord_y, offset_x, offset_y):
        return vert_coord_x + offset_x, vert_coord_y + offset_y

    vertices_base = []
    vertices_top = []
    faces = []
    cur_vert_id = 0

    for slot_id in range(header.slots_count):

        slot_x0, slot_y0 = _offset_vert_coord(
            slots_base[slot_id][0],
            slots_base[slot_id][1],
            -header.slot_half,
            -header.slot_half
            )

        slot_x1, slot_y1 = _offset_vert_coord(
            slots_base[slot_id][0],
            slots_base[slot_id][1],
            header.slot_half,
            -header.slot_half
            )

        slot_x2, slot_y2 = _offset_vert_coord(
            slots_base[slot_id][0],
            slots_base[slot_id][1],
            header.slot_half,
            header.slot_half
            )

        slot_x3, slot_y3 = _offset_vert_coord(
            slots_base[slot_id][0],
            slots_base[slot_id][1],
            -header.slot_half,
            header.slot_half
            )

        y_base = y_coords_base[slot_id]

        vertices_base.extend((
            (slot_x0, slot_y0, y_base),
            (slot_x1, slot_y1, y_base),
            (slot_x2, slot_y2, y_base),
            (slot_x3, slot_y3, y_base)
            ))

        y_top = y_coords_top[slot_id]

        vertices_top.extend((
            (slot_x0, slot_y0, y_top),
            (slot_x1, slot_y1, y_top),
            (slot_x2, slot_y2, y_top),
            (slot_x3, slot_y3, y_top)
            ))

        faces.append((
            cur_vert_id,
            cur_vert_id + 1,
            cur_vert_id + 2,
            cur_vert_id + 3
            ))

        cur_vert_id += 4

    slots_base_mesh.from_pydata(vertices_base, (), faces)
    slots_top_mesh.from_pydata(vertices_top, (), faces)

    # create UV's

    slots_base_mesh.uv_textures.new('UVMap')
    slots_top_mesh.uv_textures.new('UVMap')

    base_uv_layer_data = slots_base_mesh.uv_layers['UVMap'].data
    top_uv_layer_data = slots_top_mesh.uv_layers['UVMap'].data

    for uv_index, uv in enumerate(uvs):
        base_uv_layer_data[uv_index].uv = uv
        top_uv_layer_data[uv_index].uv = uv

    return slots_base_object, slots_top_object


def _generate_color_indices():

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


def _create_images(cx, header, meshes, root_obj, lights=None, shadows=None,
        hemi=None, lights_old=None):

    def _create_det_image(name, double_size=False):
        if double_size:
            scale = 2
        else:
            scale = 1
        bpy_image = cx.bpy.data.images.new(
            'details {0}'.format(name),
            header.size.x*scale,
            header.size.y*scale
            )
        bpy_image.use_fake_user = True
        return bpy_image

    xray = root_obj.xray
    images_list = []

    m_i = []    # meshes images
    for mesh_id in range(4):
        meshes_image = _create_det_image(
            'meshes {}'.format(mesh_id),
            double_size=True
            )
        meshes_image.use_fake_user = True
        images_list.append(meshes_image.name)
        meshes_image.pixels = meshes[mesh_id]
        m_i.append(meshes_image.name)

    xray.slots_mesh_0 = m_i[0]
    xray.slots_mesh_1 = m_i[1]
    xray.slots_mesh_2 = m_i[2]
    xray.slots_mesh_3 = m_i[3]
    del m_i

    if header.format_version == 3:

        xray.details_light_format = 'VERSION_3'

        light_image = _create_det_image('lights')
        images_list.append(light_image.name)
        light_image.pixels = lights
        del lights
        xray.lights_image = light_image.name

        shadows_image = _create_det_image('shadows')
        images_list.append(shadows_image.name)
        shadows_image.pixels = shadows
        del shadows
        xray.shadows_image = shadows_image.name

        hemi_image = _create_det_image('hemi')
        images_list.append(hemi_image.name)
        hemi_image.pixels = hemi
        del hemi
        xray.hemi_image = hemi_image.name

    elif header.format_version == 2:

        xray.details_light_format = 'VERSION_2'

        lights_v2_image = _create_det_image('lighting', double_size=True)
        images_list.append(lights_v2_image.name)
        lights_v2_image.use_fake_user = True
        lights_v2_image.pixels = lights_old
        del lights_old
        xray.lights_image = lights_v2_image.name

    if cx.details_save_slots:

        settings = cx.bpy.context.scene.render.image_settings

        file_format = settings.file_format
        if cx.save_format == 'PNG':
            settings.file_format = 'PNG'
            ext = '.png'
        if cx.save_format == 'TGA':
            settings.file_format = 'TARGA'
            ext = '.tga'

        color_mode = settings.color_mode
        color_depth = settings.color_depth
        compression = settings.compression

        settings.color_mode = 'RGBA'
        settings.color_depth = '8'
        settings.compression = 100

        for image_name in images_list:
            image = cx.bpy.data.images[image_name]
            image_path = cx.details_save_folder + image_name + ext
            image.save_render(image_path)
            image.source = 'FILE'
            image.filepath = image_path

        settings.color_mode = color_mode
        settings.color_depth = color_depth
        settings.compression = compression

        settings.file_format = file_format


def _create_pallete(cx, color_indices):

    pallete_name = 'details meshes pallete'

    # create image pallete
    if cx.bpy.data.images.get(pallete_name) == None:
        meshes_indices_pixels = []
        for color_index in color_indices:
            meshes_indices_pixels.extend(color_index)
        meshes_indices_image = cx.bpy.data.images.new(pallete_name, 64, 1)
        meshes_indices_image.pixels = meshes_indices_pixels
        meshes_indices_image.use_fake_user = True

    # create bpy pallete
    if cx.bpy.data.palettes.get(pallete_name) == None:
        pallete = cx.bpy.data.palettes.new(pallete_name)
        pallete.use_fake_user = True
        for rgba in color_indices:
            color = pallete.colors.new()
            color.color = rgba[0 : 3]   # cut alpha


def _read_details_slots(base_name, cx, pr, header, color_indices, root_obj):

    _create_pallete(cx, color_indices)

    y_coords = []
    y_coords_base = []
    meshes_images_pixels = [
        [1.0 for _ in range(header.slots_count * 4 * 4)] for _ in range(4)
        ]
    pixels_offset = {
        0: (0, 0),
        1: (1, 0),
        2: (0, 1),
        3: (1, 1),
        }

    if header.format_version == 3:
        lights_image_pixels = []
        shadows_image_pixels = []
        hemi_image_pixels = []
        S_IIHHHH = PackedReader.prep('IIHHHH')

        for slot_y in range(header.size.y):
            for slot_x in range(header.size.x):

                slot_data = pr.getp(S_IIHHHH)

                # slot Y coordinate
                y_base = slot_data[0] & 0x3ff
                y_height = (slot_data[0] >> 12) & 0xff
                y_coord_base = y_base * 0.2
                y_coord = y_coord_base + y_height * 0.1 + 0.05

                if y_coord > 100.0 or y_coord == 0.0:
                    y_coord -= 200.0
                    y_coord_base -= 200.0

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
                            pixels_offset[corner_index][0] + \
                            header.size.x * 2 * \
                            (slot_y * 2 + pixels_offset[corner_index][1])

                        color = color_indices[meshes[mesh_index]]

                        pixels = meshes_images_pixels[mesh_index]
                        pixels[pixel_index * 4] = color[0]    # Red
                        pixels[pixel_index * 4 + 1] = color[1]    # Green
                        pixels[pixel_index * 4 + 2] = color[2]    # Blue
                        pixels[pixel_index * 4 + 3] = corner_density    # Alpha

        _create_images(
            cx,
            header,
            meshes_images_pixels,
            root_obj,
            lights=lights_image_pixels,
            shadows=shadows_image_pixels,
            hemi=hemi_image_pixels
            )

    elif header.format_version == 2:
        S_ffBHBHBHBHBBBB = PackedReader.prep('ffBHBHBHBHH')
        lighting_image_pixels = [
            1.0 for _ in range(header.slots_count * 4 * 4)
            ]

        if cx.lighting_old_format == '1233':
            pixels_offset = {
                0: (0, 1),
                1: (1, 1),
                2: (0, 0),
                3: (1, 0),
                }
        elif cx.lighting_old_format == '1096':
            pixels_offset = {
                0: (0, 0),
                1: (1, 0),
                2: (0, 1),
                3: (1, 1),
                }

        density_pixels_offset = {
            0: (0, 0),
            1: (1, 0),
            2: (0, 1),
            3: (1, 1),
            }

        for slot_y in range(header.size.y):
            for slot_x in range(header.size.x):
                slot_data = pr.getp(S_ffBHBHBHBHBBBB)

                y_base = slot_data[0]
                y_top = slot_data[1]
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

        _create_images(
            cx, header, meshes_images_pixels, root_obj,
            lights_old=lighting_image_pixels
            )

    slots_base_object, slots_top_object = _create_details_slots_object(
        base_name, cx, header, y_coords, y_coords_base
        )

    return slots_base_object, slots_top_object


def _import(fpath, cx, cr):

    has_header = False
    has_meshes = False
    has_slots = False

    for chunk_id, chunk_data in cr:

        if chunk_id == 0x0 and len(chunk_data) == 0:    # bad file (build 1233)
            break

        if chunk_id == Chunks.HEADER:
            if len(chunk_data) != 24:
                raise AppError(
                    'bad details file. HEADER chunk size not equal 24'
                    )
            header = _read_header(PackedReader(chunk_data))

            if header.format_version not in SUPPORT_FORMAT_VERSIONS:
                raise AppError(
                    'unssuported details format version: {}'.format(
                        header.format_version
                        )
                    )

            has_header = True

        elif chunk_id == Chunks.MESHES:
            cr_meshes = ChunkedReader(chunk_data)
            has_meshes = True

        elif chunk_id == Chunks.SLOTS:
            if cx.load_slots:
                pr_slots = PackedReader(chunk_data)
            has_slots = True

    if not has_header:
        raise AppError('bad details file. Cannot find HEADER chunk')
    if not has_meshes:
        raise AppError('bad details file. Cannot find MESHES chunk')
    if not has_slots:
        raise AppError('bad details file. Cannot find SLOTS chunk')

    base_name = os.path.basename(fpath.lower())
    color_indices = _generate_color_indices()

    meshes_obj = _read_details_meshes(
        base_name, cx, cr_meshes, color_indices, header
        )

    if cx.load_slots:

        root_obj = cx.bpy.data.objects.new(base_name, None)
        cx.bpy.context.scene.objects.link(root_obj)

        meshes_obj.parent = root_obj

        slots_base_object, slots_top_object = _read_details_slots(
            base_name, cx, pr_slots, header, color_indices, root_obj
            )

        slots_base_object.parent = root_obj
        slots_top_object.parent = root_obj

        root_obj.xray.details_meshes_object = meshes_obj.name
        root_obj.xray.details_slots_base_object = slots_base_object.name
        root_obj.xray.details_slots_top_object = slots_top_object.name


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, cx, ChunkedReader(f.read()))
