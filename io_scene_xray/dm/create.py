# standart modules
import os

# blender modules
import bpy
import bmesh

# addon modules
from .. import text
from .. import log
from .. import utils
from .. import xray_io
from .. import version_utils


def create_object(object_name):
    bpy_mesh = bpy.data.meshes.new(object_name)
    bpy_object = bpy.data.objects.new(object_name, bpy_mesh)
    bpy_object.xray.is_details = True
    version_utils.link_object(bpy_object)
    return bpy_object, bpy_mesh


def create_empty_image(context, detail_model, absolute_image_path):
    bpy_image = bpy.data.images.new(
        os.path.basename(detail_model.texture) + '.dds', 0, 0
    )

    bpy_image.source = 'FILE'
    bpy_image.filepath = absolute_image_path
    if not version_utils.IS_28:
        bpy_image.use_alpha = True

    return bpy_image


def check_estimated_material(material, det_model):
    if not material.name.startswith(det_model.texture):
        return False

    if material.xray.eshader != det_model.shader:
        return False

    return True


def check_estimated_material_texture(material, det_model):
    texture_filepart = det_model.texture.replace('\\', os.path.sep)
    texture_found = False

    if version_utils.IS_28:
        texture_nodes = []
        for node in material.node_tree.nodes:
            if node.type in version_utils.IMAGE_NODES:
                texture_nodes.append(node)
        if len(texture_nodes) == 1:
            texture_node = texture_nodes[0]
            if texture_node.image:
                if texture_filepart in texture_node.image.filepath:
                    texture_found = True
    else:
        for texture_slot in material.texture_slots:

            if not texture_slot:
                continue

            if not hasattr(texture_slot.texture, 'image'):
                continue

            if not texture_slot.texture.image:
                continue

            if not texture_filepart in texture_slot.texture.image.filepath:
                continue

            texture_found = True

            break

    return texture_found


def find_bpy_texture(det_model, abs_image_path, alternative_image_path):
    bpy_texture = bpy.data.textures.get(det_model.texture)

    if bpy_texture:
        if not hasattr(bpy_texture, 'image'):
            bpy_texture = None
        elif not bpy_texture.image:
            bpy_texture = None
        elif bpy_texture.image.filepath != abs_image_path:
            if bpy_texture.image.filepath != alternative_image_path:
                bpy_texture = None

    return bpy_texture


def create_bpy_image(det_model, abs_image_path):
    try:
        bpy_image = bpy.data.images.load(abs_image_path)

    except RuntimeError as ex:  # e.g. 'Error: Cannot read ...'

        if det_model.mode == 'DETAILS':
            try:
                abs_image_path = os.path.abspath(
                    os.path.join(
                        os.path.dirname(det_model.file_path),
                        det_model.texture + '.dds'
                ))
                bpy_image = bpy.data.images.load(abs_image_path)
            except RuntimeError as ex:
                log.warn(text.warn.tex_not_found, path=abs_image_path)
                bpy_image = create_empty_image(
                    det_model.context,
                    det_model,
                    abs_image_path
                )

        else:
            log.warn(text.warn.tex_not_found, path=abs_image_path)
            bpy_image = create_empty_image(
                det_model.context, det_model, abs_image_path
            )

    return bpy_image


def find_bpy_image(det_model, abs_image_path):
    bpy_image = None

    for image in bpy.data.images:
        if abs_image_path == image.filepath:
            bpy_image = image
            break

    if not bpy_image:
        bpy_image = create_bpy_image(det_model, abs_image_path)

    return bpy_image


def create_bpy_texture(det_model, bpy_material, abs_image_path):
    bpy_texture = bpy.data.textures.new(det_model.texture, type='IMAGE')
    bpy_texture.use_preview_alpha = True
    bpy_texture_slot = bpy_material.texture_slots.add()
    bpy_texture_slot.texture = bpy_texture
    bpy_texture_slot.texture_coords = 'UV'
    bpy_texture_slot.uv_layer = det_model.mesh.uv_map_name
    bpy_texture_slot.use_map_color_diffuse = True
    bpy_texture_slot.use_map_alpha = True
    bpy_image = find_bpy_image(det_model, abs_image_path)
    bpy_texture.image = bpy_image


def create_material(det_model, abs_image_path, context):
    bpy_material = bpy.data.materials.new(det_model.texture)
    bpy_material.xray.eshader = det_model.shader
    bpy_material.xray.version = context.version
    if not version_utils.IS_28:
        bpy_material.use_shadeless = True
        bpy_material.use_transparency = True
        bpy_material.alpha = 0.0
        alternative_image_path = os.path.join(
            os.path.dirname(det_model.file_path),
            det_model.texture + '.dds'
        )

        bpy_texture = find_bpy_texture(
            det_model, abs_image_path, alternative_image_path
        )

        if bpy_texture is None:
            create_bpy_texture(det_model, bpy_material, abs_image_path)
        else:
            bpy_texture_slot = bpy_material.texture_slots.add()
            bpy_texture_slot.texture = bpy_texture
    else:
        bpy_material.use_nodes = True
        bpy_material.blend_method = 'CLIP'
        node_tree = bpy_material.node_tree
        texture_node = node_tree.nodes.new('ShaderNodeTexImage')
        texture_node.name = det_model.texture
        texture_node.label = det_model.texture
        bpy_image = find_bpy_image(det_model, abs_image_path)
        texture_node.image = bpy_image
        texture_node.location.x -= 500
        princ_shader = node_tree.nodes['Principled BSDF']
        node_tree.links.new(
            texture_node.outputs['Color'],
            princ_shader.inputs['Base Color']
        )
        node_tree.links.new(
            texture_node.outputs['Alpha'],
            princ_shader.inputs['Alpha']
        )

    return bpy_material


def search_material(context, det_model, file_path=None):
    abs_image_path = os.path.abspath(os.path.join(
        context.textures_folder,
        det_model.texture + '.dds'
    ))

    bpy_material = None
    bpy_image = None
    bpy_texture = None
    det_model.file_path = file_path
    det_model.context = context

    for material in bpy.data.materials:
        if not check_estimated_material(material, det_model):
            continue

        if not check_estimated_material_texture(material, det_model):
            continue

        bpy_material = material
        break

    if not bpy_material:
        bpy_material = create_material(det_model, abs_image_path, context)

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


def read_mesh_data(packed_reader, det_model):
    # read vertices coordinates and uvs
    S_FFFFF = xray_io.PackedReader.prep('fffff')
    vertices = []
    uvs = []
    for _ in range(det_model.mesh.vertices_count):
        vertex = packed_reader.getp(S_FFFFF)    # x, y, z, u, v
        vertices.append((vertex[0], vertex[2], vertex[1]))
        uvs.append((vertex[3], 1 - vertex[4]))

    # read triangles indices
    S_HHH = xray_io.PackedReader.prep('HHH')
    triangles = []
    for _ in range(det_model.mesh.indices_count // 3):
        face_indices = packed_reader.getp(S_HHH)
        triangles.append((
            face_indices[0],
            face_indices[2],
            face_indices[1]
        ))

    return vertices, uvs, triangles


def create_geometry(b_mesh, vertices, triangles):
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

    return bmesh_faces


def create_uv(b_mesh, det_model, bmesh_faces, uvs):
    uv_layer = b_mesh.loops.layers.uv.new(det_model.mesh.uv_map_name)
    uv_index = 0
    for face in bmesh_faces:
        if face:
            for loop in face.loops:
                loop[uv_layer].uv = uvs[uv_index]
                uv_index += 1
        else:
            uv_index += 3    # skip 3 loop


def create_mesh(packed_reader, det_model):
    if det_model.mesh.indices_count % 3 != 0:
        raise utils.AppError(text.error.dm_bad_indices)

    b_mesh = bmesh.new()

    vertices, uvs, triangles = read_mesh_data(packed_reader, det_model)
    vertices, uvs, triangles = reconstruct_mesh(vertices, uvs, triangles)
    bmesh_faces = create_geometry(b_mesh, vertices, triangles)
    create_uv(b_mesh, det_model, bmesh_faces, uvs)

    # assign images
    if not version_utils.IS_28:
        texture_layer = b_mesh.faces.layers.tex.new(
            det_model.mesh.uv_map_name
        )
        bpy_image = det_model.mesh.bpy_material.texture_slots[0].texture.image

        for face in b_mesh.faces:
            face[texture_layer].image = bpy_image

    b_mesh.normal_update()
    b_mesh.to_mesh(det_model.mesh.bpy_mesh)
