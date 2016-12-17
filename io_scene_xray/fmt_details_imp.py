
import os
import io
from . import fmt_details
from . import fmt_dm_imp
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
    header = DetailsHeader()
    fmt_ver, meshes_count, offs_x, offs_z, size_x, size_z = pr.getf('<IIiiII')
    header.format_version = fmt_ver
    header.meshes_count = meshes_count
    header.offset.x = offs_x
    header.offset.y = offs_z
    header.size.x = size_x
    header.size.y = size_z
    header.calc_slots_count()
    return header


def _read_details_meshes(base_name, cx, cr, color_indices):
    bpy_obj_root = cx.bpy.data.objects.new('{} meshes'.format(base_name), None)
    cx.bpy.context.scene.objects.link(bpy_obj_root)
    for mesh_id, mesh_data in cr:
        pr = PackedReader(mesh_data)
        mesh_name = '{0} mesh_{1:0>2}'.format(base_name, mesh_id)
        bpy_obj_mesh = fmt_dm_imp.import_(
            mesh_name,
            cx,
            pr,
            mode='DETAILS',
            detail_index=mesh_id,
            detail_colors=color_indices
            )
        bpy_obj_mesh.parent = bpy_obj_root
    return bpy_obj_root


def _create_details_slots_object(base_name, cx, header, y_coords):
    slots_name = '{0} slots'.format(base_name)
    slots_mesh = cx.bpy.data.meshes.new(slots_name)
    slots_object = cx.bpy.data.objects.new(slots_name, slots_mesh)
    cx.bpy.context.scene.objects.link(slots_object)
    slots = []
    uv_face_size_x = 1.0 / header.size.x
    uv_face_size_y = 1.0 / header.size.y
    uvs = []
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

            slots.append((
                (coord_x - header.offset.x) * header.slot_size + header.slot_half,
                (coord_y - header.offset.y) * header.slot_size + header.slot_half,
                y_coords[slot_id]
                ))

            slot_id += 1


    def _offset_vert_coord(vert_coord, offset_x, offset_y):
        return vert_coord[0] + offset_x, vert_coord[1] + offset_y, vert_coord[2]

    vertices = []
    faces = []
    cur_vert_id = 0
    for slot in slots:
        vertices.extend((
            (_offset_vert_coord(slot, -header.slot_half, -header.slot_half)),
            (_offset_vert_coord(slot, header.slot_half, -header.slot_half)),
            (_offset_vert_coord(slot, header.slot_half, header.slot_half)),
            (_offset_vert_coord(slot, -header.slot_half, header.slot_half))
            ))
        faces.append((
            cur_vert_id,
            cur_vert_id + 1,
            cur_vert_id + 2,
            cur_vert_id + 3
            ))
        cur_vert_id += 4
    slots_mesh.from_pydata(vertices, (), faces)

    # create UV's
    uv_textures = slots_mesh.uv_textures.new('UVMap')
    uv_layer_data = slots_mesh.uv_layers['UVMap'].data
    for uv_index, uv in enumerate(uvs):
        uv_layer_data[uv_index].uv = uv

    return slots_object


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
    mesh_ids.append([0, 0, 0])
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


def _create_images(
        cx,
        header,
        meshes,
        a_s,
        root_obj,
        lights=None,
        shadows=None,
        hemi=None,
        lights_old=None
        ):

    def _create_det_image(name):
        bpy_image = cx.bpy.data.images.new(
            'details {0}'.format(name),
            header.size.x,
            header.size.y
            )
        bpy_image.use_fake_user = True
        return bpy_image

    for mesh_id in range(4):
        meshes_image = _create_det_image('meshes {0}'.format(mesh_id))
        meshes_image.pixels = meshes[mesh_id]

    mesh_a_images = []
    for mesh_id in range(4):
        for a_id in range(4):
            a_image = _create_det_image('mesh {0} a{1}'.format(mesh_id, a_id))
            a_image.pixels = a_s[mesh_id][a_id]


    xray = root_obj.xray

    if header.format_version == 3:

        xray.details_light_format = 'VERSION_3'

        light_image = _create_det_image('lights')
        light_image.pixels = lights
        del lights
        xray.lights_image = light_image.name

        shadows_image = _create_det_image('shadows')
        shadows_image.pixels = shadows
        del shadows
        xray.shadows_image = shadows_image.name

        hemi_image = _create_det_image('hemi')
        hemi_image.pixels = hemi
        del hemi
        xray.hemi_image = hemi_image.name

    elif header.format_version == 2:

        xray.details_light_format = 'VERSION_2'

        lights_v2_image = _create_det_image('lights old')
        lights_v2_image.pixels = lights_old
        del lights_old
        xray.lights_image = lights_v2_image.name


def _read_details_slots(base_name, cx, pr, header, color_indices, root_obj):
    # create meshes id pallete
    meshes_indices_pixels = []
    for color_index in color_indices:
        meshes_indices_pixels.extend(color_index)
    meshes_indices_image = cx.bpy.data.images.new('meshes indices', 64, 1)
    meshes_indices_image.pixels = meshes_indices_pixels

    y_coords = []
    meshes_images_pixels = [[], [], [], []]
    a_s = [[[] for __ in range(4)] for _ in range(4)]
    dm_obj_in_slot_count = 4

    if header.format_version == 3:
        lights_image_pixels = []
        shadows_image_pixels = []
        hemi_image_pixels = []
        S_IIHHHH = PackedReader.prep('IIHHHH')

        for _ in range(header.slots_count):
            slot_data = pr.getp(S_IIHHHH)

            y_base = slot_data[0] & 0x3ff
            y_height = (slot_data[0] >> 12) & 0xff
            y_coord = y_base * 0.2 + y_height * 0.1
            if y_coord > 100.0 or y_coord == 0.0:
                y_coord -= 200.0
            else:
                y_coord += 5.0
            y_coords.append(y_coord)

            mesh_id_0 = (slot_data[0] >> 20) & 0x3f
            mesh_id_1 = (slot_data[0] >> 26) & 0x3f
            mesh_id_2 = slot_data[1] & 0x3f
            mesh_id_3 = (slot_data[1] >> 6) & 0x3f
            meshes_images_pixels[0].extend(color_indices[mesh_id_0])
            meshes_images_pixels[1].extend(color_indices[mesh_id_1])
            meshes_images_pixels[2].extend(color_indices[mesh_id_2])
            meshes_images_pixels[3].extend(color_indices[mesh_id_3])

            shadow = ((slot_data[1] >> 12) & 0xf) / 0xf
            shadows_image_pixels.extend((shadow, shadow, shadow, 1.0))

            hemi = ((slot_data[1] >> 16) & 0xf) / 0xf
            hemi_image_pixels.extend((hemi, hemi, hemi, 1.0))

            light_r = ((slot_data[1] >> 20) & 0xf) / 0xf
            light_g = ((slot_data[1] >> 24) & 0xf) / 0xf
            light_b = ((slot_data[1] >> 28) & 0xf) / 0xf
            lights_image_pixels.extend((light_r, light_g, light_b, 1.0))

            meshes_a_data = slot_data[2 : 6]
            for mesh_index, mesh_a_data in enumerate(meshes_a_data):
                for a_index in range(4):
                    a = ((mesh_a_data >> a_index * 4) & 0xf) / 0xf
                    a_s[mesh_index][a_index].extend((a, a, a, 1.0))

        _create_images(
            cx,
            header,
            meshes_images_pixels,
            a_s,
            root_obj,
            lights=lights_image_pixels,
            shadows=shadows_image_pixels,
            hemi=hemi_image_pixels
            )

    elif header.format_version == 2:
        S_ffBHBHBHBHBBBB = PackedReader.prep('ffBHBHBHBHH')
        lights_old_image_pixels = []

        for _ in range(header.slots_count):
            slot_data = pr.getp(S_ffBHBHBHBHBBBB)

            y_base = slot_data[0]
            y_top = slot_data[1]
            y_coords.append(y_top)

            data_index = 2

            for dm_obj_in_slot_index in range(dm_obj_in_slot_count):

                dm_obj_id = slot_data[data_index]
                if dm_obj_id == 0xff:
                    dm_obj_id = 0x3f
                meshes_images_pixels[dm_obj_in_slot_index].extend(
                    color_indices[dm_obj_id]
                    )

                palette = slot_data[data_index + 1]
                a_0123 = []
                for a_index in range(4):
                    a = ((palette >> a_index * 4) & 0xf) / 0xf
                    a_s[dm_obj_in_slot_index][a_index].extend((a, a, a, 1.0))
                data_index += 2

            for channel_index in range(4):    # R, G, B, A
                lights_old_image_pixels.append(
                    (slot_data[10] >> (channel_index * 4) & 0xf) / 0xf
                    )

        _create_images(
            cx,
            header,
            meshes_images_pixels,
            a_s,
            root_obj,
            lights_old=lights_old_image_pixels
            )

    slots_object = _create_details_slots_object(base_name, cx, header, y_coords)
    return slots_object


def _import(fpath, cx, cr):
    has_header = False
    has_meshes = False
    has_slots = False
    for chunk_id, chunk_data in cr:
        if chunk_id == fmt_details.Chunks.HEADER:
            if len(chunk_data) != 24:
                raise AppError(
                    'bad details file. HEADER chunk size not equal 24'
                    )
            header = _read_header(PackedReader(chunk_data))
            if header.format_version not in fmt_details.SUPPORT_FORMAT_VERSIONS:
                raise AppError(
                    'unssuported details format version: {}'.format(
                        header.format_version
                        )
                    )
            has_header = True
        elif chunk_id == fmt_details.Chunks.MESHES:
            cr_meshes = ChunkedReader(chunk_data)
            has_meshes = True
        elif chunk_id == fmt_details.Chunks.SLOTS:
            pr_slots = PackedReader(chunk_data)
            has_slots = True
    if not has_header:
        raise AppError('bad details file. Cannot find HEADER chunk')
    if not has_meshes:
        raise AppError('bad details file. Cannot find MESHES chunk')
    if not has_slots:
        raise AppError('bad details file. Cannot find SLOTS chunk')
    base_name = os.path.basename(fpath.lower())
    bpy_details_root_object = cx.bpy.data.objects.new(base_name, None)
    cx.bpy.context.scene.objects.link(bpy_details_root_object)

    color_indices = _generate_color_indices()
    bpy_meshes_root_object = _read_details_meshes(
                                                  base_name,
                                                  cx,
                                                  cr_meshes,
                                                  color_indices
                                                  )
    bpy_meshes_root_object.parent = bpy_details_root_object
    bpy_slots_object = _read_details_slots(
                                           base_name,
                                           cx,
                                           pr_slots,
                                           header,
                                           color_indices,
                                           bpy_details_root_object
                                           )
    bpy_slots_object.parent = bpy_details_root_object
    bpy_details_root_object.xray.details_meshes_object = bpy_meshes_root_object.name
    bpy_details_root_object.xray.details_slots_object = bpy_slots_object.name


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, cx, ChunkedReader(f.read()))
