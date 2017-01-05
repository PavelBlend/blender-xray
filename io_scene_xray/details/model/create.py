
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
