
import bpy

from . import format_


def create_object(object_name):
    bpy_mesh = bpy.data.meshes.new(object_name)
    bpy_object = bpy.data.objects.new(
        object_name, bpy_mesh
        )
    bpy.context.scene.objects.link(bpy_object)
    return bpy_object, bpy_mesh


def create_details_slots_object(base_name, header, y_coords_top, y_coords_base):
    slots_base_object, slots_base_mesh = create_object(
        '{0} slots base'.format(base_name)
    )
    slots_top_object, slots_top_mesh = create_object(
        '{0} slots top'.format(base_name)
    )

    slots_base = []
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

            slot_id += 1

    def _offset_vert_coord(vert_coord_x, vert_coord_y, offset_x, offset_y):
        return vert_coord_x + offset_x, vert_coord_y + offset_y

    vertices_base = []
    vertices_top = []
    faces = []
    cur_vert_id = 0

    offset_signs = ((-1, -1), (+1, -1), (+1, +1), (-1, +1))

    for slot_id in range(header.slots_count):

        y_base = y_coords_base[slot_id]
        y_top = y_coords_top[slot_id]

        for corner_index in range(4):
            slot_x, slot_y = _offset_vert_coord(
                slots_base[slot_id][0],
                slots_base[slot_id][1],
                offset_signs[corner_index][0] * header.slot_half,
                offset_signs[corner_index][1] * header.slot_half
                )
            vertices_base.append((slot_x, slot_y, y_base))
            vertices_top.append((slot_x, slot_y, y_top))

        faces.append((
            cur_vert_id,
            cur_vert_id + 1,
            cur_vert_id + 2,
            cur_vert_id + 3
            ))

        cur_vert_id += 4

    del slots_base

    slots_base_mesh.from_pydata(vertices_base, (), faces)

    del vertices_base

    slots_top_mesh.from_pydata(vertices_top, (), faces)

    del vertices_top, faces

    # create UV's

    slots_base_mesh.uv_textures.new('UVMap')
    slots_top_mesh.uv_textures.new('UVMap')

    base_uv_layer_data = slots_base_mesh.uv_layers['UVMap'].data
    top_uv_layer_data = slots_top_mesh.uv_layers['UVMap'].data

    for uv_index, uv in enumerate(uvs):
        base_uv_layer_data[uv_index].uv = uv
        top_uv_layer_data[uv_index].uv = uv

    return slots_base_object, slots_top_object


def create_images(header, meshes, root_obj, lights=None, shadows=None,
                  hemi=None, lights_old=None):

    def _create_det_image(name, double_size=False):
        if double_size:
            scale = 2
        else:
            scale = 1
        bpy_image = bpy.data.images.new(
            'details {0}'.format(name),
            header.size.x*scale,
            header.size.y*scale
            )
        bpy_image.use_fake_user = True
        return bpy_image

    slots = root_obj.xray.detail.slots
    dets_meshes = slots.meshes
    ligthing = slots.ligthing

    images_list = []

    m_i = []    # meshes images
    for mesh_id in range(4):
        meshes_image = _create_det_image(
            'meshes {}.png'.format(mesh_id),
            double_size=True
            )
        meshes_image.use_fake_user = True
        images_list.append(meshes_image.name)
        meshes_image.pixels = meshes[mesh_id]
        meshes_image.pack(as_png=True)
        m_i.append(meshes_image.name)

    dets_meshes.mesh_0 = m_i[0]
    dets_meshes.mesh_1 = m_i[1]
    dets_meshes.mesh_2 = m_i[2]
    dets_meshes.mesh_3 = m_i[3]

    if header.format_version == format_.FORMAT_VERSION_3:

        ligthing.format = 'builds_1569-cop'

        image_names = ('lights', 'shadows', 'hemi')
        pixels = (lights, shadows, hemi)
        props = ('lights_image', 'shadows_image', 'hemi_image')

        for image_name, pixels, prop_name in zip(image_names, pixels, props):
            bpy_image = _create_det_image('{}.png'.format(image_name))
            images_list.append(bpy_image.name)
            bpy_image.pixels = pixels
            bpy_image.pack(as_png=True)
            setattr(ligthing, prop_name, bpy_image.name)

    elif header.format_version == format_.FORMAT_VERSION_2:

        ligthing.format = 'builds_1096-1558'

        lights_v2_image = _create_det_image('lighting.png', double_size=True)
        images_list.append(lights_v2_image.name)
        lights_v2_image.use_fake_user = True
        lights_v2_image.pixels = lights_old
        lights_v2_image.pack(as_png=True)
        ligthing.lights_image = lights_v2_image.name


def create_pallete(color_indices):

    pallete_name = 'details meshes pallete.png'

    # create image pallete
    if bpy.data.images.get(pallete_name) is None:
        meshes_indices_pixels = []
        for color_index in color_indices:
            meshes_indices_pixels.extend(color_index)
        meshes_indices_image = bpy.data.images.new(
            pallete_name, format_.DETAIL_MODEL_COUNT_LIMIT + 1, 1
        )
        meshes_indices_image.pixels = meshes_indices_pixels
        meshes_indices_image.use_fake_user = True
        meshes_indices_image.pack(as_png=True)

    # create bpy pallete
    if bpy.data.palettes.get(pallete_name) is None:
        pallete = bpy.data.palettes.new(pallete_name)
        pallete.use_fake_user = True
        for rgba in color_indices:
            color = pallete.colors.new()
            color.color = rgba[0 : 3]   # cut alpha
