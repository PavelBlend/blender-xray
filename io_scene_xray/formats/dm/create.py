# standart modules
import os

# blender modules
import bpy
import bmesh

# addon modules
from ... import text
from ... import log
from ... import utils
from ... import rw


def create_object(object_name):
    bpy_mesh = bpy.data.meshes.new(object_name)
    bpy_object = bpy.data.objects.new(object_name, bpy_mesh)
    bpy_object.xray.is_details = True
    utils.version.link_object(bpy_object)
    utils.stats.created_obj()
    utils.stats.created_msh()
    return bpy_object, bpy_mesh


def check_estimated_material(material, det_model):
    if not material.name.startswith(det_model.texture):
        return False

    if material.xray.eshader != det_model.shader:
        return False

    return True


def check_estimated_material_texture(material, det_model):
    texture_filepart = det_model.texture.replace('\\', os.path.sep)
    texture_found = False

    if utils.version.IS_28:
        texture_nodes = []
        for node in material.node_tree.nodes:
            if node.type in utils.version.IMAGE_NODES:
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


def create_bpy_texture(det_model, bpy_material, context):
    bpy_texture = bpy.data.textures.new(det_model.texture, type='IMAGE')
    bpy_texture.use_preview_alpha = True
    bpy_texture_slot = bpy_material.texture_slots.add()
    bpy_texture_slot.texture = bpy_texture
    bpy_texture_slot.texture_coords = 'UV'
    bpy_texture_slot.uv_layer = det_model.mesh.uv_map_name
    bpy_texture_slot.use_map_color_diffuse = True
    bpy_texture_slot.use_map_alpha = True
    bpy_image = context.image(det_model.texture)
    bpy_texture.image = bpy_image
    utils.stats.created_tex()


def create_material(det_model, abs_image_path, context):
    bpy_material = bpy.data.materials.new(det_model.texture)
    bpy_material.xray.eshader = det_model.shader
    bpy_material.xray.version = context.version
    utils.stats.created_mat()

    if utils.version.IS_28:
        bpy_material.use_nodes = True
        bpy_material.blend_method = 'CLIP'
        node_tree = bpy_material.node_tree

        # remove material nodes
        node_tree.nodes.clear()

        princ_shader = utils.material.create_mat_nodes(bpy_material)
        bpy_image = context.image(det_model.texture)

        # texture node
        texture_node = node_tree.nodes.new('ShaderNodeTexImage')
        texture_node.name = det_model.texture
        texture_node.label = det_model.texture
        texture_node.image = bpy_image
        texture_node.select = False
        texture_node.location.x = princ_shader.location.x - 500.0

        # link nodes
        node_tree.links.new(
            texture_node.outputs['Color'],
            princ_shader.inputs['Base Color']
        )
        node_tree.links.new(
            texture_node.outputs['Alpha'],
            princ_shader.inputs['Alpha']
        )

    else:
        bpy_material.use_shadeless = True
        bpy_material.use_transparency = True
        bpy_material.alpha = 0.0
        alternative_image_path = os.path.join(
            os.path.dirname(det_model.file_path),
            det_model.texture + '.dds'
        )

        bpy_texture = utils.tex.search_texture_by_tex_path(det_model.texture, abs_image_path)

        if bpy_texture is None:
            create_bpy_texture(det_model, bpy_material, context)
        else:
            bpy_texture_slot = bpy_material.texture_slots.add()
            bpy_texture_slot.texture = bpy_texture

    return bpy_material


def search_material(context, det_model, file_path=None):
    abs_image_path = os.path.abspath(os.path.join(
        context.tex_folder,
        det_model.texture + '.dds'
    ))

    bpy_material = None
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
    for vert_1, vert_2, vert_3 in triangles:
        remap_triangles.append((
            remap_indices[vert_1],
            remap_indices[vert_2],
            remap_indices[vert_3]
        ))
        remap_uvs.extend((
            uvs[vert_1],
            uvs[vert_2],
            uvs[vert_3]
        ))

    return remap_vertices, remap_uvs, remap_triangles


def read_mesh_data(packed_reader, det_model):
    # read vertices coordinates and uvs
    S_FFFFF = rw.read.PackedReader.prep('5f')
    vertices = []
    uvs = []
    for _ in range(det_model.mesh.vertices_count):
        co_x, co_y, co_z, co_u, co_v = packed_reader.getp(S_FFFFF)
        vertices.append((co_x, co_z, co_y))
        uvs.append((co_u, 1.0 - co_v))

    # read triangles indices
    S_HHH = rw.read.PackedReader.prep('3H')
    triangles = []
    for _ in range(det_model.mesh.indices_count // 3):
        vert_1, vert_2, vert_3 = packed_reader.getp(S_HHH)
        triangles.append((vert_1, vert_3, vert_2))

    return vertices, uvs, triangles


def create_geometry(b_mesh, vertices, triangles):
    # create vertices
    for vertex_coord in vertices:
        b_mesh.verts.new(vertex_coord)
    b_mesh.verts.ensure_lookup_table()

    # create triangles
    bmesh_faces = []
    for vert_1, vert_2, vert_3 in triangles:
        try:
            bmesh_face = b_mesh.faces.new((
                b_mesh.verts[vert_1],
                b_mesh.verts[vert_2],
                b_mesh.verts[vert_3]
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
    if det_model.mesh.indices_count % 3:
        raise log.AppError(text.error.dm_bad_indices)

    b_mesh = bmesh.new()

    vertices, uvs, triangles = read_mesh_data(packed_reader, det_model)
    vertices, uvs, triangles = reconstruct_mesh(vertices, uvs, triangles)
    bmesh_faces = create_geometry(b_mesh, vertices, triangles)
    create_uv(b_mesh, det_model, bmesh_faces, uvs)

    # assign images
    if not utils.version.IS_28:
        texture_layer = b_mesh.faces.layers.tex.new(
            det_model.mesh.uv_map_name
        )
        bpy_image = det_model.mesh.bpy_material.texture_slots[0].texture.image

        for face in b_mesh.faces:
            face[texture_layer].image = bpy_image

    b_mesh.normal_update()
    b_mesh.to_mesh(det_model.mesh.bpy_mesh)
