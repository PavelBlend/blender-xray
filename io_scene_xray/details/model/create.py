
def create_object(cx, object_name):
    bpy_mesh = cx.bpy.data.meshes.new(object_name)
    bpy_obj = cx.bpy.data.objects.new(object_name, bpy_mesh)
    cx.bpy.context.scene.objects.link(bpy_obj)
    return bpy_obj, bpy_mesh


def search_material(cx, dm):

    abs_image_path = cx.os.path.abspath(
        cx.os.path.join(cx.textures_folder, dm.texture + '.dds')
        )

    bpy_material = None
    bpy_image = None
    bpy_texture = None

    for material in cx.bpy.data.materials:

        if not material.name.startswith(dm.texture):
            continue

        if material.xray.eshader != dm.shader:
            continue

        tx_filepart = dm.texture.replace('\\', cx.os.path.sep)
        ts_found = False

        for ts in material.texture_slots:

            if not ts:
                continue

            if ts.uv_layer != dm.mesh.uv_map_name:
                continue

            if not hasattr(ts.texture, 'image'):
                continue

            if not tx_filepart in ts.texture.image.filepath:
                continue

            ts_found = True

            break

        if not ts_found:
            continue

        bpy_material = material
        break

    if not bpy_material:

        bpy_material = cx.bpy.data.materials.new(dm.texture)
        bpy_material.xray.eshader = dm.shader
        bpy_material.use_shadeless = True
        bpy_material.use_transparency = True
        bpy_material.alpha = 0.0
        bpy_texture = cx.bpy.data.textures.get(dm.texture)

        if bpy_texture:
            if not hasattr(bpy_texture, 'image'):
                bpy_texture = None
            else:
                if bpy_texture.image.filepath != abs_image_path:
                    bpy_texture = None

        if bpy_texture is None:
            bpy_texture = cx.bpy.data.textures.new(dm.texture, type='IMAGE')
            bpy_texture.use_preview_alpha = True
            bpy_texture_slot = bpy_material.texture_slots.add()
            bpy_texture_slot.texture = bpy_texture
            bpy_texture_slot.texture_coords = 'UV'
            bpy_texture_slot.uv_layer = dm.mesh.uv_map_name
            bpy_texture_slot.use_map_color_diffuse = True
            bpy_texture_slot.use_map_alpha = True
            bpy_image = None

            for bi in cx.bpy.data.images:
                if abs_image_path == bi.filepath:
                    bpy_image = bi
                    break
    
            if not bpy_image:

                try:
                    bpy_image = cx.bpy.data.images.load(abs_image_path)

                except RuntimeError as ex:  # e.g. 'Error: Cannot read ...'
                    cx.report({'WARNING'}, str(ex))

                    bpy_image = cx.bpy.data.images.new(
                        cx.os.path.basename(dm.texture) + '.dds', 0, 0
                        )

                    bpy_image.source = 'FILE'

                    if not cx.textures_folder:
                        bpy_image.filepath = dm.texture + '.dds'
                    else:
                        bpy_image.filepath = abs_image_path

                    bpy_image.use_alpha = True
    
            bpy_texture.image = bpy_image

        else:
            bpy_texture_slot = bpy_material.texture_slots.add()
            bpy_texture_slot.texture = bpy_texture

    return bpy_material


def create_mesh(cx, pr, dm, PackedReader):

    from io_scene_xray.utils import AppError

    if dm.mesh.indices_count % 3 != 0:
        raise AppError('bad dm triangle indices')

    import bmesh

    bm = bmesh.new()

    S_FFFFF = PackedReader.prep('fffff')    

    uvs = {}

    for _ in range(dm.mesh.vertices_count):
        v = pr.getp(S_FFFFF)    # x, y, z, u, v
        bm_vert = bm.verts.new((v[0], v[2], v[1]))
        uvs[bm_vert] = (v[3], v[4])

    bm.verts.ensure_lookup_table()
    S_HHH = PackedReader.prep('HHH')

    for _ in range(dm.mesh.indices_count // 3):

        fi = pr.getp(S_HHH)    # face indices

        try:
            bm.faces.new(
                (bm.verts[fi[0]], bm.verts[fi[2]], bm.verts[fi[1]])
                ).smooth = True
        except ValueError:
            pass

    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.new(dm.mesh.uv_map_name)

    if dm.mode == 'DM':
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_layer].uv = uvs[loop.vert]

    elif dm.mode == 'DETAILS':
        for face in bm.faces:
            for loop in face.loops:
                uv = uvs[loop.vert]
                loop[uv_layer].uv = uv[0], 1 - uv[1]

    else:
        raise Exception(
            'unknown dm import mode: {0}. ' \
            'You must use DM or DETAILS'.format(dm.mode)
            )

    bml_tex = bm.faces.layers.tex.new(dm.mesh.uv_map_name)
    bpy_image = dm.mesh.bpy_material.texture_slots[0].texture.image

    for bmf in bm.faces:
        bmf[bml_tex].image = bpy_image

    bm.normal_update()
    bm.to_mesh(dm.mesh.bpy_mesh)
