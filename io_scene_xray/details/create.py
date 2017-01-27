
def create_details_slots_object(base_name, cx, header, y_coords_top,
        y_coords_base):

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


def create_images(cx, header, meshes, root_obj, lights=None, shadows=None,
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

    s = root_obj.xray.detail.slots
    m = s.meshes
    l = s.ligthing

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

    m.mesh_0 = m_i[0]
    m.mesh_1 = m_i[1]
    m.mesh_2 = m_i[2]
    m.mesh_3 = m_i[3]

    if header.format_version == 3:

        l.format = 'builds_1569-cop'

        light_image = _create_det_image('lights')
        images_list.append(light_image.name)
        light_image.pixels = lights
        l.lights_image = light_image.name

        shadows_image = _create_det_image('shadows')
        images_list.append(shadows_image.name)
        shadows_image.pixels = shadows
        l.shadows_image = shadows_image.name

        hemi_image = _create_det_image('hemi')
        images_list.append(hemi_image.name)
        hemi_image.pixels = hemi
        l.hemi_image = hemi_image.name

    elif header.format_version == 2:

        l.format = 'builds_1096-1558'

        lights_v2_image = _create_det_image('lighting', double_size=True)
        images_list.append(lights_v2_image.name)
        lights_v2_image.use_fake_user = True
        lights_v2_image.pixels = lights_old
        l.lights_image = lights_v2_image.name

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


def create_pallete(cx, color_indices):

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
