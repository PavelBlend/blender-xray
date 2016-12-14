
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


def _read_header(pr):
    header = DetailsHeader()
    fmt_ver, meshes_count, offs_x, offs_z, size_x, size_z = pr.getf('<IIiiII')
    header.format_version = fmt_ver
    header.meshes_count = meshes_count
    header.offset.x = offs_x
    header.offset.y = offs_z
    header.size.x = size_x
    header.size.y = size_z
    return header


def _read_details_meshes(fpath, cx, cr):
    base_name = os.path.basename(fpath.lower())
    root_object = cx.bpy.data.objects.new(base_name, None)
    cx.bpy.context.scene.objects.link(root_object)
    for mesh_id, mesh_data in cr:
        pr = PackedReader(mesh_data)
        mesh_name = '{0} mesh_{1:0>2}'.format(base_name, mesh_id)
        bpy_obj = fmt_dm_imp.import_(mesh_name, cx, pr, mode='DETAILS')
        bpy_obj.parent = root_object


def _read_details_slots(fpath, cx, pr, header):

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
                mesh_id[2] / color_depth
                )
            color_indices.append(color_index)
        return color_indices

    S_IIHHHH = PackedReader.prep('IIHHHH')
    y_coords = []
    lights = []
    shadows = []
    light_hemi = []
    meshes_ids = []
    a_s = []
    color_indices = _generate_color_indices()
    for _ in range(header.size.x * header.size.y):
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
        meshes_ids.append((
            color_indices[mesh_id_0],
            color_indices[mesh_id_1],
            color_indices[mesh_id_2],
            color_indices[mesh_id_3]
            ))
        shadow = ((slot_data[1] >> 12) & 0xf) / 0xf
        shadows.append(shadow)
        hemi = ((slot_data[1] >> 16) & 0xf) / 0xf
        light_hemi.append(hemi)
        light_r = ((slot_data[1] >> 20) & 0xf) / 0xf
        light_g = ((slot_data[1] >> 24) & 0xf) / 0xf
        light_b = ((slot_data[1] >> 28) & 0xf) / 0xf
        lights.append((light_r, light_g, light_b))
        a_0123 = [[], [], [], []]
        for i in range(2, 6):
            a0 = ((slot_data[i] >> 0) & 0xf) / 0xf
            a1 = ((slot_data[i] >> 4) & 0xf) / 0xf
            a2 = ((slot_data[i] >> 8) & 0xf) / 0xf
            a3 = ((slot_data[i] >> 12) & 0xf) / 0xf
            a_0123[i - 2].extend((a0, a1, a2, a3))
        a_s.append(a_0123)
    base_name = os.path.basename(fpath.lower())
    slots_name = '{0} slots'.format(base_name)
    slots_mesh = cx.bpy.data.meshes.new(slots_name)
    slots_object = cx.bpy.data.objects.new(slots_name, slots_mesh)
    cx.bpy.context.scene.objects.link(slots_object)
    slots_count = header.size.x * header.size.y
    coord_x = 0
    coord_y = 0
    coord_z = 0
    slots = []
    for slot_id in range(slots_count):
        if not slot_id % header.size.x and slot_id:
            coord_x -= header.size.x - 1
            coord_y += 1
        else:
            coord_x += 1
        slots.append((
            (coord_x - 1 - header.offset.x) * header.slot_size + header.slot_half,
            (coord_y - header.offset.y) * header.slot_size + header.slot_half,
            y_coords[slot_id]
            ))

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

    def _create_image(name):
        return cx.bpy.data.images.new(
            'details {0}'.format(name),
            header.size.x,
            header.size.y
            )

    light_image = _create_image('lights')
    shadows_image = _create_image('shadows')
    hemi_image = _create_image('hemi')
    # meshes ids
    meshes_images = []
    for index in range(4):
        meshes_images.append(_create_image('meshes {0}'.format(index)))
    # meshes a
    mesh_a_images = []
    for mesh_id in range(4):
        for a_id in range(4):
            mesh_a_images.append(
                _create_image('mesh {0} a{1}'.format(mesh_id, a_id))
                )
    light_image_pixels = []
    shadows_image_pixels = []
    hemi_image_pixels = []
    meshes_images_pixels = [[], [], [], []]
    a_s_pixels = [[[] for __ in range(4)] for _ in range(4)]
    for slot_index in range(header.size.x * header.size.y):
        light = lights[slot_index]
        shadow = shadows[slot_index]
        hemi = light_hemi[slot_index]
        mesh_id = meshes_ids[slot_index]
        slot_a = a_s[slot_index]
        red_channel = slot_index * 4
        green_channel = red_channel + 1
        blue_channel = green_channel + 1
        light_image_pixels.extend((light[0], light[1], light[2], 1.0))
        shadows_image_pixels.extend((shadow, shadow, shadow, 1.0))
        hemi_image_pixels.extend((hemi, hemi, hemi, 1.0))
        # meshes id
        for i in range(4):
            meshes_images_pixels[i].extend((
                mesh_id[i][0],
                mesh_id[i][1],
                mesh_id[i][2],
                1.0
                ))
        # mesh a
        for mesh_id in range(4):
            mesh_a = slot_a[mesh_id]
            for a_id in range(4):
                a_s_pixels[mesh_id][a_id].extend((mesh_a[a_id], mesh_a[a_id], mesh_a[a_id], 1.0))
    # assign pixels
    light_image.pixels = light_image_pixels
    shadows_image.pixels = shadows_image_pixels
    hemi_image.pixels = hemi_image_pixels
    for image_id, pixels in enumerate(meshes_images_pixels):
        meshes_images[image_id].pixels = pixels
    image_id = 0
    for mesh_id in range(4):
        for a_id in range(4):
            mesh_a_images[image_id].pixels = a_s_pixels[mesh_id][a_id]
            image_id += 1


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
    _read_details_meshes(fpath, cx, cr_meshes)
    _read_details_slots(fpath, cx, pr_slots, header)


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, cx, ChunkedReader(f.read()))
