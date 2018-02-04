
import bpy
import bmesh
from ...xray_io import PackedReader


def create_object(object_name):
    bpy_mesh = bpy.data.meshes.new(object_name)
    bpy_obj = bpy.data.objects.new(object_name, bpy_mesh)
    bpy.context.scene.objects.link(bpy_obj)
    return bpy_obj, bpy_mesh


def create_empty_image(context, det_model, abs_image_path):
    bpy_image = bpy.data.images.new(
        context.os.path.basename(det_model.texture) + '.dds', 0, 0
        )

    bpy_image.source = 'FILE'

    if not context.textures_folder:
        bpy_image.filepath = det_model.texture + '.dds'
    else:
        bpy_image.filepath = abs_image_path

    bpy_image.use_alpha = True


def search_material(context, det_model, fpath=None):

    abs_image_path = context.os.path.abspath(
        context.os.path.join(context.textures_folder, det_model.texture + '.dds')
        )

    bpy_material = None
    bpy_image = None
    bpy_texture = None

    for material in bpy.data.materials:

        if not material.name.startswith(det_model.texture):
            continue

        if material.xray.eshader != det_model.shader:
            continue

        tx_filepart = det_model.texture.replace('\\', context.os.path.sep)
        ts_found = False

        for texture_slot in material.texture_slots:

            if not texture_slot:
                continue

            if texture_slot.uv_layer != det_model.mesh.uv_map_name:
                continue

            if not hasattr(texture_slot.texture, 'image'):
                continue

            if not texture_slot.texture.image:
                continue

            if not tx_filepart in texture_slot.texture.image.filepath:
                continue

            ts_found = True

            break

        if not ts_found:
            continue

        bpy_material = material
        break

    if not bpy_material:

        bpy_material = bpy.data.materials.new(det_model.texture)
        bpy_material.xray.eshader = det_model.shader
        bpy_material.use_shadeless = True
        bpy_material.use_transparency = True
        bpy_material.alpha = 0.0
        bpy_texture = bpy.data.textures.get(det_model.texture)

        if bpy_texture:
            if not hasattr(bpy_texture, 'image'):
                bpy_texture = None
            elif not bpy_texture.image:
                bpy_texture = None
            else:
                if bpy_texture.image.filepath != abs_image_path:
                    bpy_texture = None

        if bpy_texture is None:
            bpy_texture = bpy.data.textures.new(det_model.texture, type='IMAGE')
            bpy_texture.use_preview_alpha = True
            bpy_texture_slot = bpy_material.texture_slots.add()
            bpy_texture_slot.texture = bpy_texture
            bpy_texture_slot.texture_coords = 'UV'
            bpy_texture_slot.uv_layer = det_model.mesh.uv_map_name
            bpy_texture_slot.use_map_color_diffuse = True
            bpy_texture_slot.use_map_alpha = True
            bpy_image = None

            for image in bpy.data.images:
                if abs_image_path == image.filepath:
                    bpy_image = image
                    break

            if not bpy_image:

                try:
                    bpy_image = bpy.data.images.load(abs_image_path)

                except RuntimeError as ex:  # e.g. 'Error: Cannot read ...'

                    if det_model.mode == 'DETAILS':
                        try:
                            abs_image_path = context.os.path.abspath(
                                context.os.path.join(
                                    context.os.path.dirname(fpath),
                                    det_model.texture + '.dds'
                            ))
                            bpy_image = bpy.data.images.load(abs_image_path)
                        except RuntimeError as ex:
                            context.report({'WARNING'}, str(ex))
                            create_empty_image(context, det_model, abs_image_path)

                    else:
                        context.report({'WARNING'}, str(ex))
                        create_empty_image(context, det_model, abs_image_path)

            bpy_texture.image = bpy_image

        else:
            bpy_texture_slot = bpy_material.texture_slots.add()
            bpy_texture_slot.texture = bpy_texture

    return bpy_material


def create_mesh(packed_reader, det_model):

    from ...utils import AppError

    if det_model.mesh.indices_count % 3 != 0:
        raise AppError('bad dm triangle indices')

    b_mesh = bmesh.new()

    S_FFFFF = PackedReader.prep('fffff')

    uvs = {}

    for _ in range(det_model.mesh.vertices_count):
        vertex = packed_reader.getp(S_FFFFF)    # x, y, z, u, v
        bm_vert = b_mesh.verts.new((vertex[0], vertex[2], vertex[1]))
        uvs[bm_vert] = (vertex[3], vertex[4])

    b_mesh.verts.ensure_lookup_table()
    S_HHH = PackedReader.prep('HHH')

    for _ in range(det_model.mesh.indices_count // 3):

        face_indices = packed_reader.getp(S_HHH)    # face indices

        try:
            b_mesh.faces.new((
                b_mesh.verts[face_indices[0]],
                b_mesh.verts[face_indices[2]],
                b_mesh.verts[face_indices[1]])
                            ).smooth = True
        except ValueError:
            pass

    b_mesh.faces.ensure_lookup_table()
    uv_layer = b_mesh.loops.layers.uv.new(det_model.mesh.uv_map_name)

    if det_model.mode == 'DM':
        for face in b_mesh.faces:
            for loop in face.loops:
                loop[uv_layer].uv = uvs[loop.vert]

    elif det_model.mode == 'DETAILS':
        for face in b_mesh.faces:
            for loop in face.loops:
                uv = uvs[loop.vert]
                loop[uv_layer].uv = uv[0], 1 - uv[1]

    else:
        raise Exception(
            'unknown dm import mode: {0}. ' \
            'You must use DM or DETAILS'.format(det_model.mode)
            )

    bml_tex = b_mesh.faces.layers.tex.new(det_model.mesh.uv_map_name)
    bpy_image = det_model.mesh.bpy_material.texture_slots[0].texture.image

    for bmf in b_mesh.faces:
        bmf[bml_tex].image = bpy_image

    b_mesh.normal_update()
    b_mesh.to_mesh(det_model.mesh.bpy_mesh)
