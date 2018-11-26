
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
    bpy_image.filepath = abs_image_path
    bpy_image.use_alpha = True
    return bpy_image


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
                            bpy_image = create_empty_image(context, det_model, abs_image_path)

                    else:
                        context.report({'WARNING'}, str(ex))
                        bpy_image = create_empty_image(context, det_model, abs_image_path)

            bpy_texture.image = bpy_image

        else:
            bpy_texture_slot = bpy_material.texture_slots.add()
            bpy_texture_slot.texture = bpy_texture

    return bpy_material


def reconstruct_mesh(vertices, uvs, triangles):

    # remove doubles vertices
    loaded_vertices = {}
    remap_vertices = []
    remap_indices = {}
    remap_index = 0
    for vertex_index, vertex_coord in enumerate(vertices):
        if loaded_vertices.get(vertex_coord):
            remap_indices[vertex_index] = loaded_vertices[vertex_coord]
        else:
            loaded_vertices[vertex_coord] = remap_index
            remap_indices[vertex_index] = remap_index
            remap_vertices.append(vertex_coord)
            remap_index += 1

    # generate new triangles indices and uvs
    remap_triangles = []
    remap_uvs = []
    for triangle in triangles:
        remap_triangles.append((
            remap_indices[triangle[0]],
            remap_indices[triangle[1]],
            remap_indices[triangle[2]]
        ))
        for vertex_index in triangle:
            remap_uvs.append(uvs[vertex_index])

    return remap_vertices, remap_uvs, remap_triangles


def create_mesh(packed_reader, det_model):

    from ...utils import AppError

    if det_model.mesh.indices_count % 3 != 0:
        raise AppError('bad dm triangle indices')

    b_mesh = bmesh.new()

    # read vertices coordinates and uvs
    S_FFFFF = PackedReader.prep('fffff')
    vertices = []
    uvs = []
    for _ in range(det_model.mesh.vertices_count):
        vertex = packed_reader.getp(S_FFFFF)    # x, y, z, u, v
        vertices.append((vertex[0], vertex[2], vertex[1]))
        uvs.append((vertex[3], vertex[4]))

    # read triangles indices
    S_HHH = PackedReader.prep('HHH')
    triangles = []
    for _ in range(det_model.mesh.indices_count // 3):
        face_indices = packed_reader.getp(S_HHH)
        triangles.append((face_indices[0], face_indices[2], face_indices[1]))

    # reconstruct mesh
    vertices, uvs, triangles = reconstruct_mesh(vertices, uvs, triangles)

    # create vertices
    for vertex_coord in vertices:
        b_mesh.verts.new(vertex_coord)
    b_mesh.verts.ensure_lookup_table()

    # create triangles
    bmesh_faces = []
    for triangle in triangles:
        try:
            bmesh_face = b_mesh.faces.new((
                b_mesh.verts[triangle[0]],
                b_mesh.verts[triangle[1]],
                b_mesh.verts[triangle[2]]
            ))
            bmesh_face.smooth = True
            bmesh_faces.append(bmesh_face)
        except ValueError:
            bmesh_faces.append(None)
    b_mesh.faces.ensure_lookup_table()

    # create uvs
    uv_layer = b_mesh.loops.layers.uv.new(det_model.mesh.uv_map_name)

    if det_model.mode == 'DM':
        uv_index = 0
        for face in bmesh_faces:
            if face:
                for loop in face.loops:
                    loop[uv_layer].uv = uvs[uv_index]
                    uv_index += 1
            else:
                uv_index += 3    # skip 3 loop

    elif det_model.mode == 'DETAILS':
        uv_index = 0
        for face in bmesh_faces:
            if face:
                for loop in face.loops:
                    uv = uvs[uv_index]
                    loop[uv_layer].uv = uv[0], 1 - uv[1]
                    uv_index += 1
            else:
                uv_index += 3    # skip 3 loop

    else:
        raise Exception(
            'unknown dm import mode: {0}. ' \
            'You must use DM or DETAILS'.format(det_model.mode)
            )

    # assign images
    bml_tex = b_mesh.faces.layers.tex.new(det_model.mesh.uv_map_name)
    bpy_image = det_model.mesh.bpy_material.texture_slots[0].texture.image

    for bmf in b_mesh.faces:
        bmf[bml_tex].image = bpy_image

    b_mesh.normal_update()
    b_mesh.to_mesh(det_model.mesh.bpy_mesh)
