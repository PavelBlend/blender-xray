# standart modules
import math

# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import fmt
from .. import text
from .. import create
from .. import omf
from .. import log
from .. import utils
from .. import xray_io
from .. import version_utils
from .. import ie_utils
from .. import level
from .. import xray_motions


class Visual(object):
    def __init__(self):
        self.file_path = None
        self.visual_id = None
        self.format_version = None
        self.model_type = None
        self.shader_id = None
        self.texture_id = None
        self.name = None
        self.vertices = None
        self.uvs = None
        self.uvs_lmap = None
        self.triangles = None
        self.indices_count = None
        self.indices = None
        self.weights = None
        self.hemi = None
        self.sun = None
        self.light = None
        self.fastpath = False
        self.use_two_sided_tris = False
        self.vb_index = None
        self.is_root = None
        self.bpy_materials = None
        self.arm_obj = None
        self.root_obj = None
        self.bones = None
        self.deform_bones = None
        self.motion_refs = None
        self.create_name = None
        self.create_time = None
        self.modif_name = None
        self.modif_time = None
        self.user_data = None
        self.lod = None


class HierrarhyVisual(object):
    def __init__(self):
        self.index = None
        self.children = []
        self.children_count = None


def get_material(lvl, shader_id, texture_id):
    material_key = (shader_id, texture_id)
    bpy_material = lvl.materials.get(material_key, None)
    if not bpy_material:
        if not (lvl.shaders and lvl.textures):
            shader_raw = lvl.shaders_or_textures[shader_id]
            texture_raw = lvl.shaders_or_textures[texture_id]
            shader_data = shader_raw + '/' + texture_raw
            bpy_material, bpy_image = level.shaders.import_shader(
                lvl, lvl.context, shader_data
            )
        else:
            shader_raw = lvl.shaders[shader_id]
            texture_raw = lvl.textures[texture_id]
            shader_data = shader_raw + '/' + texture_raw
            bpy_material, bpy_image = level.shaders.import_shader(
                lvl, lvl.context, shader_data
            )
        lvl.materials[material_key] = bpy_material
        lvl.images[texture_id] = bpy_image
    return bpy_material


def assign_material(bpy_mesh, visual, lvl):
    if (
            visual.format_version == fmt.FORMAT_VERSION_4 or
            lvl.xrlc_version >= level.fmt.VERSION_12
        ):
        shader_id = visual.shader_id
        bpy_material = lvl.materials[shader_id]
        if visual.use_two_sided_tris:
            bpy_material.xray.flags_twosided = True
    else:
        bpy_material = get_material(lvl, visual.shader_id, visual.texture_id)
    bpy_mesh.materials.append(bpy_material)


def create_object(name, obj_data):
    bpy_object = bpy.data.objects.new(name, obj_data)
    version_utils.link_object(bpy_object)
    return bpy_object


def convert_normal(norm_in):
    norm_out_x = 2.0 * norm_in[0] / 255 - 1.0
    norm_out_y = 2.0 * norm_in[1] / 255 - 1.0
    norm_out_z = 2.0 * norm_in[2] / 255 - 1.0
    return mathutils.Vector((norm_out_z, norm_out_x, norm_out_y)).normalized()


def convert_float_normal(norm_in):
    return mathutils.Vector((norm_in[2], norm_in[0], norm_in[1])).normalized()


def create_visual(visual, bpy_mesh=None, lvl=None, geometry_key=None, bones=None):
    if not bpy_mesh:
        mesh = bmesh.new()

        temp_mesh = bmesh.new()

        remap_vertex_index = 0
        remap_vertices = {}
        unique_verts = {}
        vert_normals = {}
        for vertex_index, vertex_coord in enumerate(visual.vertices):
            vert = temp_mesh.verts.new(vertex_coord)
            vert_normals[tuple(vert.co)] = []

        temp_mesh.verts.ensure_lookup_table()
        temp_mesh.verts.index_update()

        for triangle in visual.triangles:
            temp_mesh.faces.new((
                temp_mesh.verts[triangle[0]],
                temp_mesh.verts[triangle[1]],
                temp_mesh.verts[triangle[2]]
            ))

        temp_mesh.faces.ensure_lookup_table()
        temp_mesh.normal_update()

        back_side = {}

        for vert in temp_mesh.verts:
            norm = (
                round(vert.normal[0], 3),
                round(vert.normal[1], 3),
                round(vert.normal[2], 3)
            )
            vert_normals[tuple(vert.co)].append((vert.index, norm))

        temp_mesh.clear()
        del temp_mesh

        for vertex_co, norms in vert_normals.items():
            back_side_norms = set()
            for vertex_index, normal in norms:
                normal = tuple(normal)
                back_norm = (-normal[0], -normal[1], -normal[2])
                if back_norm in back_side_norms:
                    back_side[vertex_index] = True
                else:
                    back_side[vertex_index] = False
                    back_side_norms.add(normal)

        # import vertices
        remap_vertex_index = 0
        remap_vertices = {}
        unique_verts = {}
        if not visual.weights:
            for vertex_index, vertex_coord in enumerate(visual.vertices):
                is_back_vert = back_side[vertex_index]
                if unique_verts.get((vertex_coord, is_back_vert), None) is None:
                    mesh.verts.new(vertex_coord)
                    remap_vertices[vertex_index] = remap_vertex_index
                    unique_verts[(vertex_coord, is_back_vert)] = remap_vertex_index
                    remap_vertex_index += 1
                else:
                    current_remap_vertex_index = unique_verts[(vertex_coord, is_back_vert)]
                    remap_vertices[vertex_index] = current_remap_vertex_index
        else:
            for vertex_index, vertex_coord in enumerate(visual.vertices):
                is_back_vert = back_side[vertex_index]
                weights = tuple(visual.weights[vertex_index])
                if unique_verts.get((vertex_coord, weights, is_back_vert), None) is None:
                    mesh.verts.new(vertex_coord)
                    remap_vertices[vertex_index] = remap_vertex_index
                    unique_verts[(vertex_coord, weights, is_back_vert)] = remap_vertex_index
                    remap_vertex_index += 1
                else:
                    current_remap_vertex_index = unique_verts[(vertex_coord, weights, is_back_vert)]
                    remap_vertices[vertex_index] = current_remap_vertex_index

        mesh.verts.ensure_lookup_table()
        mesh.verts.index_update()

        # import triangles
        remap_loops = []
        custom_normals = []
        if not visual.vb_index is None:
            if not lvl.vertex_buffers[visual.vb_index].float_normals:
                convert_normal_function = convert_normal
        else:
            convert_normal_function = convert_float_normal
        is_new_format = False
        if lvl:
            if lvl.xrlc_version >= level.fmt.VERSION_11:
                is_new_format = True
        else:
            if visual.format_version == fmt.FORMAT_VERSION_4:
                is_new_format = True
        if is_new_format:
            for triangle in visual.triangles:
                try:
                    vert_1 = remap_vertices[triangle[0]]
                    vert_2 = remap_vertices[triangle[1]]
                    vert_3 = remap_vertices[triangle[2]]
                    face = mesh.faces.new((
                        mesh.verts[vert_1],
                        mesh.verts[vert_2],
                        mesh.verts[vert_3]
                    ))
                    face.smooth = True
                    for vert_index in triangle:
                        remap_loops.append(vert_index)
                    normal_1 = visual.normals[triangle[0]]
                    normal_2 = visual.normals[triangle[1]]
                    normal_3 = visual.normals[triangle[2]]
                    custom_normals.extend((
                        convert_normal_function(normal_1),
                        convert_normal_function(normal_2),
                        convert_normal_function(normal_3)
                    ))
                except ValueError:    # face already exists
                    pass

            mesh.faces.ensure_lookup_table()

            # import uvs and vertex colors
            uv_layer = mesh.loops.layers.uv.new('Texture')
            hemi_vertex_color = mesh.loops.layers.color.new('Hemi')
            current_loop = 0
            if visual.uvs_lmap:    # light maps
                lmap_uv_layer = mesh.loops.layers.uv.new('Light Map')
                for face in mesh.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                        loop[lmap_uv_layer].uv = visual.uvs_lmap[remap_loops[current_loop]]
                        # hemi vertex color
                        hemi = visual.hemi[remap_loops[current_loop]]
                        bmesh_hemi_color = loop[hemi_vertex_color]
                        bmesh_hemi_color[0] = hemi
                        bmesh_hemi_color[1] = hemi
                        bmesh_hemi_color[2] = hemi
                        current_loop += 1
            elif visual.light:    # vertex colors
                sun_vertex_color = mesh.loops.layers.color.new('Sun')
                light_vertex_color = mesh.loops.layers.color.new('Light')
                for face in mesh.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                        # hemi vertex color
                        hemi = visual.hemi[remap_loops[current_loop]]
                        bmesh_hemi_color = loop[hemi_vertex_color]
                        bmesh_hemi_color[0] = hemi
                        bmesh_hemi_color[1] = hemi
                        bmesh_hemi_color[2] = hemi
                        # light vertex color
                        light = visual.light[remap_loops[current_loop]]
                        bmesh_light_color = loop[light_vertex_color]
                        bmesh_light_color[0] = light[0]
                        bmesh_light_color[1] = light[1]
                        bmesh_light_color[2] = light[2]
                        # sun vertex color
                        sun = visual.sun[remap_loops[current_loop]]
                        bmesh_sun_color = loop[sun_vertex_color]
                        bmesh_sun_color[0] = sun
                        bmesh_sun_color[1] = sun
                        bmesh_sun_color[2] = sun
                        current_loop += 1
            else:
                if visual.hemi:    # trees
                    for face in mesh.faces:
                        for loop in face.loops:
                            loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                            # hemi vertex color
                            hemi = visual.hemi[remap_loops[current_loop]]
                            bmesh_hemi_color = loop[hemi_vertex_color]
                            bmesh_hemi_color[0] = hemi
                            bmesh_hemi_color[1] = hemi
                            bmesh_hemi_color[2] = hemi
                            current_loop += 1
                else:    # ogf file
                    for face in mesh.faces:
                        for loop in face.loops:
                            loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                            current_loop += 1

        else:    # xrlc version <= 10
            if visual.normals:
                for triangle in visual.triangles:
                    try:
                        vert_1 = remap_vertices[triangle[0]]
                        vert_2 = remap_vertices[triangle[1]]
                        vert_3 = remap_vertices[triangle[2]]
                        face = mesh.faces.new((
                            mesh.verts[vert_1],
                            mesh.verts[vert_2],
                            mesh.verts[vert_3]
                        ))
                        face.smooth = True
                        for vert_index in triangle:
                            remap_loops.append(vert_index)
                        normal_1 = visual.normals[triangle[0]]
                        normal_2 = visual.normals[triangle[1]]
                        normal_3 = visual.normals[triangle[2]]
                        custom_normals.extend((
                            convert_normal(normal_1),
                            convert_normal(normal_2),
                            convert_normal(normal_3)
                        ))
                    except ValueError:    # face already exists
                        pass
            else:
                for triangle in visual.triangles:
                    try:
                        vert_1 = remap_vertices[triangle[0]]
                        vert_2 = remap_vertices[triangle[1]]
                        vert_3 = remap_vertices[triangle[2]]
                        face = mesh.faces.new((
                            mesh.verts[vert_1],
                            mesh.verts[vert_2],
                            mesh.verts[vert_3]
                        ))
                        face.smooth = True
                        for vert_index in triangle:
                            remap_loops.append(vert_index)
                    except ValueError:    # face already exists
                        pass

            mesh.faces.ensure_lookup_table()

            # import uvs and vertex colors
            uv_layer = mesh.loops.layers.uv.new('Texture')
            current_loop = 0
            if visual.uvs_lmap:    # light maps
                lmap_uv_layer = mesh.loops.layers.uv.new('Light Map')
                for face in mesh.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                        loop[lmap_uv_layer].uv = visual.uvs_lmap[remap_loops[current_loop]]
                        current_loop += 1
            elif visual.light:    # vertex colors
                light_vertex_color = mesh.loops.layers.color.new('Light')
                for face in mesh.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                        # light vertex color
                        light = visual.light[remap_loops[current_loop]]
                        bmesh_light_color = loop[light_vertex_color]
                        bmesh_light_color[0] = light[0]
                        bmesh_light_color[1] = light[1]
                        bmesh_light_color[2] = light[2]
                        current_loop += 1
            else:
                for face in mesh.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = visual.uvs[remap_loops[current_loop]]
                        current_loop += 1

        # normals
        mesh.normal_update()

        # create mesh
        bpy_mesh = bpy.data.meshes.new(visual.name)
        bpy_mesh.use_auto_smooth = True
        bpy_mesh.auto_smooth_angle = math.pi
        if lvl:
            assign_material(bpy_mesh, visual, lvl)

            if not version_utils.IS_28:
                bpy_image = lvl.images[visual.shader_id]
                texture_layer = mesh.faces.layers.tex.new('Texture')
                for face in mesh.faces:
                    face[texture_layer].image = bpy_image

            lvl.loaded_geometry[geometry_key] = bpy_mesh

        else:
            material = visual.bpy_materials[visual.shader_id]
            bpy_mesh.materials.append(material)

        mesh.to_mesh(bpy_mesh)
        if custom_normals:
            bpy_mesh.normals_split_custom_set(custom_normals)
        del mesh

    else:
        if lvl:
            bpy_mesh = lvl.loaded_geometry[geometry_key]

    bpy_object = create_object(visual.name, bpy_mesh)

    # assign weights
    if visual.weights:
        for index, (name, parent) in enumerate(visual.bones):
            if index in visual.deform_bones:
                bpy_object.vertex_groups.new(name=name)
        for index, weights in enumerate(visual.weights):
            for bone_index, weight in weights:
                bone_name, _ = visual.bones[bone_index]
                group = bpy_object.vertex_groups[bone_name]
                vert_index = remap_vertices[index]
                group.add([vert_index, ], weight, 'REPLACE')

    return bpy_object


def import_fastpath_gcontainer(data, visual, lvl):
    packed_reader = xray_io.PackedReader(data)

    vb_index = packed_reader.getf('<I')[0]
    vb_offset = packed_reader.getf('<I')[0]
    vb_size = packed_reader.getf('<I')[0]
    ib_index = packed_reader.getf('<I')[0]
    ib_offset = packed_reader.getf('<I')[0]
    ib_size = packed_reader.getf('<I')[0]

    vb_slice = slice(vb_offset, vb_offset + vb_size)
    geometry_key = (vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size)
    bpy_mesh = lvl.loaded_fastpath_geometry.get(geometry_key, None)
    if bpy_mesh:
        return bpy_mesh, geometry_key
    vertex_buffers = lvl.fastpath_vertex_buffers
    indices_buffers = lvl.fastpath_indices_buffers
    visual.vertices = vertex_buffers[vb_index].position[vb_slice]

    visual.indices = indices_buffers[ib_index][
        ib_offset : ib_offset + ib_size
    ]
    visual.indices_count = ib_size

    return bpy_mesh, geometry_key


def read_gcontainer_v4(data):
    packed_reader = xray_io.PackedReader(data)

    vb_index = packed_reader.getf('<I')[0]
    vb_offset = packed_reader.getf('<I')[0]
    vb_size = packed_reader.getf('<I')[0]
    ib_index = packed_reader.getf('<I')[0]
    ib_offset = packed_reader.getf('<I')[0]
    ib_size = packed_reader.getf('<I')[0]

    return vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size


def import_gcontainer(
        visual, lvl,
        vb_index, vb_offset, vb_size,
        ib_index, ib_offset, ib_size
    ):

    if not (vb_index is None and vb_offset is None and vb_size is None):
        vb_slice = slice(vb_offset, vb_offset + vb_size)
        geometry_key = (vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size)
        bpy_mesh = lvl.loaded_geometry.get(geometry_key, None)
        if bpy_mesh:
            return bpy_mesh, geometry_key
        vertex_buffers = lvl.vertex_buffers
        indices_buffers = lvl.indices_buffers
        visual.vertices = vertex_buffers[vb_index].position[vb_slice]
        visual.normals = vertex_buffers[vb_index].normal[vb_slice]
        visual.uvs = vertex_buffers[vb_index].uv[vb_slice]
        visual.uvs_lmap = vertex_buffers[vb_index].uv_lmap[vb_slice]
        visual.hemi = vertex_buffers[vb_index].color_hemi[vb_slice]
        visual.vb_index = vb_index

        if vertex_buffers[vb_index].color_light:
            visual.light = vertex_buffers[vb_index].color_light[vb_slice]
        if vertex_buffers[vb_index].color_sun:
            visual.sun = vertex_buffers[vb_index].color_sun[vb_slice]
    else:
        bpy_mesh = None
        geometry_key = None

    if not (ib_index is None and ib_offset is None and ib_size is None):
        visual.indices = indices_buffers[ib_index][
            ib_offset : ib_offset + ib_size
        ]
        visual.indices_count = ib_size

    return bpy_mesh, geometry_key


def import_vcontainer(data):
    pass


def read_indices(packed_reader):
    indices_count = packed_reader.getf('<I')[0]
    indices_buffer = packed_reader.getf('<{0}H'.format(indices_count))
    return indices_buffer, indices_count


def import_indices(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.INDICES)
    packed_reader = xray_io.PackedReader(chunk_data)
    visual.indices, visual.indices_count = read_indices(packed_reader)


def read_indices_v3(data, visual):
    packed_reader = xray_io.PackedReader(data)
    indices_count = packed_reader.getf('<I')[0]
    visual.indices_count = indices_count
    visual.indices = [
        packed_reader.getf('<H')[0]
        for index in range(indices_count)
    ]


def read_vertices_v3(data, visual, lvl):
    packed_reader = xray_io.PackedReader(data)
    vb = level.vb.import_vertex_buffer_d3d7(packed_reader, lvl)
    visual.vertices = vb.position
    visual.normals = vb.normal
    visual.uvs = vb.uv
    visual.uvs_lmap = vb.uv_lmap


def import_skeleton_vertices(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.VERTICES)
    packed_reader = xray_io.PackedReader(chunk_data)
    vertex_format = packed_reader.getf('<I')[0]
    verices_count = packed_reader.getf('<I')[0]
    vertices = []
    normals = []
    uvs = []
    weights = []
    visual.deform_bones = set()
    if vertex_format in (fmt.VertexFormat.FVF_1L, fmt.VertexFormat.FVF_1L_CS):
        for vertex_index in range(verices_count):
            coords = packed_reader.getv3f()
            normal = packed_reader.getn3f()
            tangent = packed_reader.getn3f()
            bitangent = packed_reader.getn3f()
            tex_u, tex_v = packed_reader.getf('<2f')
            bone_index = packed_reader.getf('<I')[0]
            vertices.append(coords)
            normals.append(normal)
            uvs.append((tex_u, 1 - tex_v))
            vertex_weights = [(bone_index, 1), ]
            weights.append(vertex_weights)
            visual.deform_bones.add(bone_index)
    elif vertex_format in (fmt.VertexFormat.FVF_2L, fmt.VertexFormat.FVF_2L_CS):
        for vertex_index in range(verices_count):
            bone_1_index = packed_reader.getf('<H')[0]
            bone_2_index = packed_reader.getf('<H')[0]
            coords = packed_reader.getv3f()
            normal = packed_reader.getn3f()
            tangent = packed_reader.getn3f()
            bitangent = packed_reader.getn3f()
            weight = packed_reader.getf('<f')[0]
            tex_u, tex_v = packed_reader.getf('<2f')
            vertices.append(coords)
            normals.append(normal)
            uvs.append((tex_u, 1 - tex_v))
            if bone_1_index != bone_2_index:
                vertex_weights = [
                    (bone_1_index, 1 - weight),
                    (bone_2_index, weight),
                ]
            else:
                vertex_weights = [(bone_1_index, 1), ]
            weights.append(vertex_weights)
            visual.deform_bones.update((bone_1_index, bone_2_index))
    elif vertex_format == fmt.VertexFormat.FVF_3L_CS:
        for vertex_index in range(verices_count):
            bone_1_index = packed_reader.getf('<H')[0]
            bone_2_index = packed_reader.getf('<H')[0]
            bone_3_index = packed_reader.getf('<H')[0]
            coords = packed_reader.getv3f()
            normal = packed_reader.getn3f()
            tangent = packed_reader.getn3f()
            bitangent = packed_reader.getn3f()
            weight_1, weight_2 = packed_reader.getf('<2f')
            weight_3 = 1 - weight_1 - weight_2
            tex_u, tex_v = packed_reader.getf('<2f')
            vertices.append(coords)
            normals.append(normal)
            uvs.append((tex_u, 1 - tex_v))
            vertex_weights = []
            bone_indices = [bone_1_index, bone_2_index, bone_3_index]
            bone_weights = [weight_1, weight_2, weight_3]
            used_bones = []
            for bone, weight in zip(bone_indices, bone_weights):
                if bone in used_bones:
                    continue
                used_bones.append(bone)
                vertex_weights.append((bone, weight))
            weights.append(vertex_weights)
            visual.deform_bones.update((
                bone_1_index,
                bone_2_index,
                bone_3_index
            ))
    elif vertex_format == fmt.VertexFormat.FVF_4L_CS:
        for vertex_index in range(verices_count):
            bone_1_index = packed_reader.getf('<H')[0]
            bone_2_index = packed_reader.getf('<H')[0]
            bone_3_index = packed_reader.getf('<H')[0]
            bone_4_index = packed_reader.getf('<H')[0]
            coords = packed_reader.getv3f()
            normal = packed_reader.getn3f()
            tangent = packed_reader.getn3f()
            bitangent = packed_reader.getn3f()
            weight_1, weight_2, weight_3 = packed_reader.getf('<3f')
            weight_4 = 1 - weight_1 - weight_2 - weight_3
            tex_u, tex_v = packed_reader.getf('<2f')
            vertices.append(coords)
            normals.append(normal)
            uvs.append((tex_u, 1 - tex_v))
            bone_indices = (
                bone_1_index,
                bone_2_index,
                bone_3_index,
                bone_4_index
            )
            bone_weights = (weight_1, weight_2, weight_3, weight_4)
            used_bones = []
            vertex_weights = []
            for bone, weight in zip(bone_indices, bone_weights):
                if bone in used_bones:
                    continue
                used_bones.append(bone)
                vertex_weights.append((bone, weight))
            weights.append(vertex_weights)
            visual.deform_bones.update((
                bone_1_index,
                bone_2_index,
                bone_3_index,
                bone_4_index
            ))
    else:
        raise utils.AppError(
            text.error.ogf_bad_vertex_fmt,
            log.props(vertex_format=hex(vertex_format))
        )
    visual.vertices = vertices
    visual.normals = normals
    visual.uvs = uvs
    visual.weights = weights


def import_vertices(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.VERTICES)
    packed_reader = xray_io.PackedReader(chunk_data)
    vertex_format = packed_reader.getf('<I')[0]
    verices_count = packed_reader.getf('<I')[0]
    vertices = []
    normals = []
    uvs = []
    if vertex_format == level.fmt.FVF_OGF:
        for vertex_index in range(verices_count):
            coords = packed_reader.getv3f()
            normal = packed_reader.getn3f()
            tex_u, tex_v = packed_reader.getf('<2f')
            vertices.append(coords)
            normals.append(normal)
            uvs.append((tex_u, 1 - tex_v))
    else:
        raise utils.AppError(
            text.error.ogf_bad_vertex_fmt,
            log.props(vertex_format=vertex_format)
        )
    visual.vertices = vertices
    visual.normals = normals
    visual.uvs = uvs


def import_fastpath(data, visual, lvl):
    chunked_reader = xray_io.ChunkedReader(data)
    chunks = {}
    for chunk_id, chunkd_data in chunked_reader:
        chunks[chunk_id] = chunkd_data
    del chunked_reader

    gcontainer_chunk_data = chunks.pop(fmt.Chunks_v4.GCONTAINER)
    import_fastpath_gcontainer(gcontainer_chunk_data, visual, lvl)
    del gcontainer_chunk_data

    swi_chunk_data = chunks.pop(fmt.Chunks_v4.SWIDATA, None)
    if swi_chunk_data:
        packed_reader = xray_io.PackedReader(swi_chunk_data)
        swi = level.swi.import_slide_window_item(packed_reader)
        visual.indices = visual.indices[swi[0].offset : ]
        visual.indices_count = swi[0].triangles_count * 3
        del swi_chunk_data

    for chunk_id in chunks.keys():
        print('UNKNOW OGF FASTPATH CHUNK: {0:#x}'.format(chunk_id))


def check_unread_chunks(chunks, context=''):
    chunks_ids = list(chunks.keys())
    chunks_ids.sort()
    if chunks:
        print('There are OGF unread {1} chunks: {0}'.format(
            list(map(hex, chunks_ids)), context
        ))


def import_children_l(data, visual, lvl, visual_type):
    packed_reader = xray_io.PackedReader(data)
    hierrarhy_visual = HierrarhyVisual()
    hierrarhy_visual.children_count = packed_reader.getf('<I')[0]
    hierrarhy_visual.index = visual.visual_id
    hierrarhy_visual.visual_type = visual_type

    if len(data) == 4 + 4 * hierrarhy_visual.children_count:
        child_format = 'I'
    elif len(data) == 4 + 2 * hierrarhy_visual.children_count:
        # used in agroprom 2215 (version 13)
        child_format = 'H'
    else:
        raise BaseException('Bad OGF CHILDREN_L data')

    for child_index in range(hierrarhy_visual.children_count):
        child = packed_reader.getf('<' + child_format)[0]
        hierrarhy_visual.children.append(child)

    lvl.hierrarhy_visuals.append(hierrarhy_visual)


def import_hierrarhy_visual(chunks, visual, lvl):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        chunks_ids = fmt.Chunks_v4
    elif visual.format_version in (fmt.FORMAT_VERSION_3, fmt.FORMAT_VERSION_2):

        if visual.format_version == fmt.FORMAT_VERSION_3:
            chunks_ids = fmt.Chunks_v3
        else:
            chunks_ids = fmt.Chunks_v2

        # bbox
        bbox_data = chunks.pop(chunks_ids.BBOX)
        read_bbox_v3(bbox_data)

        # bsphere
        bsphere_data = chunks.pop(chunks_ids.BSPHERE, None)
        if bsphere_data:
            read_bsphere_v3(bsphere_data)

    visual.name = 'hierrarhy'
    children_l_data = chunks.pop(chunks_ids.CHILDREN_L)
    import_children_l(children_l_data, visual, lvl, 'HIERRARHY')
    del children_l_data
    bpy_object = create_object(visual.name, None)
    check_unread_chunks(chunks, context='HIERRARHY_VISUAL')
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'HIERRARHY'
    return bpy_object


def read_bbox_v3(data):
    packed_reader = xray_io.PackedReader(data)

    bbox_min = packed_reader.getf('<3f')
    bbox_max = packed_reader.getf('<3f')


def read_bsphere_v3(data):
    packed_reader = xray_io.PackedReader(data)

    center = packed_reader.getf('<3f')
    radius = packed_reader.getf('<f')[0]


def read_container_v3(data):
    packed_reader = xray_io.PackedReader(data)

    buffer_index = packed_reader.getf('<I')[0]
    buffer_offset = packed_reader.getf('<I')[0]
    buffer_size = packed_reader.getf('<I')[0]

    return buffer_index, buffer_offset, buffer_size


def import_geometry(chunks, visual, lvl):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        chunks_ids = fmt.Chunks_v4
        gcontainer_data = chunks.pop(chunks_ids.GCONTAINER, None)
        if gcontainer_data:
            vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size = read_gcontainer_v4(gcontainer_data)
            del gcontainer_data
        else:
            # vcontainer
            vcontainer_data = chunks.pop(chunks_ids.VCONTAINER)
            vb_index, vb_offset, vb_size = read_container_v3(vcontainer_data)

            # icontainer
            icontainer_data = chunks.pop(chunks_ids.ICONTAINER)
            ib_index, ib_offset, ib_size = read_container_v3(icontainer_data)

        fastpath_data = chunks.pop(chunks_ids.FASTPATH, None)    # optional chunk
        if fastpath_data:
            visual.fastpath = True
        else:
            visual.fastpath = False
        del fastpath_data

    elif visual.format_version in (fmt.FORMAT_VERSION_3, fmt.FORMAT_VERSION_2):

        if visual.format_version == fmt.FORMAT_VERSION_3:
            chunks_ids = fmt.Chunks_v3
        else:
            chunks_ids = fmt.Chunks_v2

        # bbox
        bbox_data = chunks.pop(chunks_ids.BBOX)
        read_bbox_v3(bbox_data)

        # bsphere
        bsphere_data = chunks.pop(chunks_ids.BSPHERE)
        read_bsphere_v3(bsphere_data)

        # vcontainer
        vcontainer_data = chunks.pop(chunks_ids.VCONTAINER, None)
        if vcontainer_data:
            vb_index, vb_offset, vb_size = read_container_v3(vcontainer_data)
        else:
            vertices_data = chunks.pop(chunks_ids.VERTICES)
            read_vertices_v3(vertices_data, visual, lvl)
            vb_index = None
            vb_offset = None
            vb_size = None

        # icontainer
        icontainer_data = chunks.pop(chunks_ids.ICONTAINER, None)
        if icontainer_data:
            ib_index, ib_offset, ib_size = read_container_v3(icontainer_data)
        else:
            indices_data = chunks.pop(chunks_ids.INDICES)
            read_indices_v3(indices_data, visual)
            ib_index = None
            ib_offset = None
            ib_size = None

    bpy_mesh, geometry_key = import_gcontainer(
        visual, lvl,
        vb_index, vb_offset, vb_size,
        ib_index, ib_offset, ib_size
    )

    return bpy_mesh, geometry_key


def convert_indices_to_triangles(visual):
    visual.triangles = []
    for index in range(0, visual.indices_count, 3):
        visual.triangles.append((
            visual.indices[index],
            visual.indices[index + 2],
            visual.indices[index + 1]
        ))
    del visual.indices
    del visual.indices_count


def import_normal_visual(chunks, visual, lvl):
    visual.name = 'normal'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, lvl)
    check_unread_chunks(chunks, context='NORMAL_VISUAL')

    if not bpy_mesh:
        convert_indices_to_triangles(visual)
        bpy_object = create_visual(visual, bpy_mesh, lvl, geometry_key)
        if visual.fastpath:
            bpy_object.xray.level.use_fastpath = True
        else:
            bpy_object.xray.level.use_fastpath = False
    else:
        bpy_object = create_object(visual.name, bpy_mesh)

    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'NORMAL'
    return bpy_object


def ogf_color(lvl, packed_reader, bpy_obj, mode='SCALE'):
    xray_level = bpy_obj.xray.level

    if lvl.xrlc_version >= level.fmt.VERSION_11:
        rgb = packed_reader.getf('<3f')
        hemi = packed_reader.getf('<f')[0]
        sun = packed_reader.getf('<f')[0]
    else:
        rgb = packed_reader.getf('<3f')
        hemi = packed_reader.getf('<f')[0]    # unkonwn
        sun = 1.0

    if mode == 'SCALE':
        xray_level.color_scale_rgb = rgb
        xray_level.color_scale_hemi = (hemi, hemi, hemi)
        xray_level.color_scale_sun = (sun, sun, sun)
    elif mode == 'BIAS':
        xray_level.color_bias_rgb = rgb
        xray_level.color_bias_hemi = (hemi, hemi, hemi)
        xray_level.color_bias_sun = (sun, sun, sun)
    else:
        raise utils.AppError(
            text.error.ogf_bad_color_mode,
            log.props(mode=mode)
        )


def import_tree_def_2(lvl, visual, chunks, bpy_object):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        chunks_ids = fmt.Chunks_v4
    elif visual.format_version == fmt.FORMAT_VERSION_3:
        chunks_ids = fmt.Chunks_v3

    tree_def_2_data = chunks.pop(chunks_ids.TREEDEF2)
    packed_reader = xray_io.PackedReader(tree_def_2_data)
    del tree_def_2_data

    tree_xform = packed_reader.getf('<16f')
    ogf_color(lvl, packed_reader, bpy_object, mode='SCALE')    # c_scale
    ogf_color(lvl, packed_reader, bpy_object, mode='BIAS')    # c_bias

    return tree_xform


def set_tree_transforms(bpy_object, xform):
    transform_matrix = mathutils.Matrix((
        (xform[0], xform[1], xform[2], xform[3]),
        (xform[4], xform[5], xform[6], xform[7]),
        (xform[8], xform[9], xform[10], xform[11]),
        (xform[12], xform[13], xform[14], xform[15])
        ))
    transform_matrix.transpose()
    translate, rotate, scale = transform_matrix.decompose()
    bpy_object.location = translate[0], translate[2], translate[1]
    bpy_object.scale = scale[0], scale[2], scale[1]
    rotate = rotate.to_euler('ZXY')
    bpy_object.rotation_euler = -rotate[0], -rotate[2], -rotate[1]


def import_tree_st_visual(chunks, visual, lvl):
    visual.name = 'tree_st'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, lvl)
    if not bpy_mesh:
        convert_indices_to_triangles(visual)
        bpy_object = create_visual(visual, bpy_mesh, lvl, geometry_key)
    else:
        bpy_object = create_object(visual.name, bpy_mesh)
    tree_xform = import_tree_def_2(lvl, visual, chunks, bpy_object)
    set_tree_transforms(bpy_object, tree_xform)
    check_unread_chunks(chunks, context='TREE_ST_VISUAL')
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'TREE_ST'
    return bpy_object


def import_swidata(chunks):
    swi_data = chunks.pop(fmt.Chunks_v4.SWIDATA)
    packed_reader = xray_io.PackedReader(swi_data)
    del swi_data
    swi = level.swi.import_slide_window_item(packed_reader)
    del packed_reader
    return swi


def import_progressive_visual(chunks, visual, lvl):
    visual.name = 'progressive'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, lvl)
    swi = import_swidata(chunks)

    visual.indices = visual.indices[swi[0].offset : ]
    visual.indices_count = swi[0].triangles_count * 3
    convert_indices_to_triangles(visual)

    check_unread_chunks(chunks, context='PROGRESSIVE_VISUAL')

    if not bpy_mesh:
        bpy_object = create_visual(visual, bpy_mesh, lvl, geometry_key)
        if visual.fastpath:
            bpy_object.xray.level.use_fastpath = True
        else:
            bpy_object.xray.level.use_fastpath = False
    else:
        bpy_object = create_object(visual.name, bpy_mesh)

    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'PROGRESSIVE'
    return bpy_object


def import_swicontainer(chunks):
    swicontainer_data = chunks.pop(fmt.Chunks_v4.SWICONTAINER)
    packed_reader = xray_io.PackedReader(swicontainer_data)
    del swicontainer_data
    swi_index = packed_reader.getf('<I')[0]
    return swi_index


def get_float_rgb_hemi(rgb_hemi):
    hemi = (rgb_hemi & (0xff << 24)) >> 24
    red = (rgb_hemi & (0xff << 16)) >> 16
    green = (rgb_hemi & (0xff << 8)) >> 8
    blue = rgb_hemi & 0xff
    return red / 0xff, green / 0xff, blue / 0xff, hemi / 0xff


def import_lod_def_2(lvl, data):
    packed_reader = xray_io.PackedReader(data)
    verts = []
    uvs = []
    lights = {'rgb': [], 'hemi': [], 'sun': []}
    faces = []
    if lvl.xrlc_version >= level.fmt.VERSION_11:
        for face_index in range(8):
            face = []
            for vert_index in range(4):
                coord_x, coord_y, coord_z = packed_reader.getf('<3f')
                verts.append((coord_x, coord_z, coord_y))
                face.append(face_index * 4 + vert_index)
                coord_u, coord_v = packed_reader.getf('<2f')
                uvs.append((coord_u, 1 - coord_v))
                # import vertex light
                rgb_hemi = packed_reader.getf('<I')[0]
                red, green, blue, hemi = get_float_rgb_hemi(rgb_hemi)
                sun = packed_reader.getf('<B')[0]
                sun = sun / 0xff
                packed_reader.getf('<3B')    # pad (unused)
                lights['rgb'].append((red, green, blue, 1.0))
                lights['hemi'].append(hemi)
                lights['sun'].append(sun)
            faces.append(face)
    else:
        for face_index in range(8):
            face = []
            for vert_index in range(4):
                coord_x, coord_y, coord_z = packed_reader.getf('<3f')
                verts.append((coord_x, coord_z, coord_y))
                face.append(face_index * 4 + vert_index)
                coord_u, coord_v = packed_reader.getf('<2f')
                uvs.append((coord_u, 1 - coord_v))
                # import vertex light
                rgb_hemi = packed_reader.getf('<I')[0]
                red, green, blue, hemi = get_float_rgb_hemi(rgb_hemi)
                lights['rgb'].append((red, green, blue, 1.0))
                lights['hemi'].append(1.0)
                lights['sun'].append(1.0)
            faces.append(face)
    return verts, uvs, lights, faces


def import_lod_visual(chunks, visual, lvl):
    if visual.format_version == fmt.FORMAT_VERSION_4:
        chunks_ids = fmt.Chunks_v4
    elif visual.format_version == fmt.FORMAT_VERSION_3:
        chunks_ids = fmt.Chunks_v3

        # bbox
        bbox_data = chunks.pop(chunks_ids.BBOX)
        read_bbox_v3(bbox_data)

        # bsphere
        bsphere_data = chunks.pop(chunks_ids.BSPHERE)
        read_bsphere_v3(bsphere_data)

    visual.name = 'lod'
    children_l_data = chunks.pop(chunks_ids.CHILDREN_L)
    import_children_l(children_l_data, visual, lvl, 'LOD')
    del children_l_data

    lod_def_2_data = chunks.pop(chunks_ids.LODDEF2)
    verts, uvs, lights, faces = import_lod_def_2(lvl, lod_def_2_data)
    del lod_def_2_data

    check_unread_chunks(chunks, context='LOD_VISUAL')

    bpy_mesh = bpy.data.meshes.new(visual.name)
    bpy_mesh.from_pydata(verts, (), faces)
    if version_utils.IS_28:
        uv_layer = bpy_mesh.uv_layers.new(name='Texture')
    else:
        uv_texture = bpy_mesh.uv_textures.new(name='Texture')
        uv_layer = bpy_mesh.uv_layers[uv_texture.name]
    rgb_color = bpy_mesh.vertex_colors.new(name='Light')
    hemi_color = bpy_mesh.vertex_colors.new(name='Hemi')
    sun_color = bpy_mesh.vertex_colors.new(name='Sun')
    if version_utils.IS_28:
        for face in bpy_mesh.polygons:
            for loop_index in face.loop_indices:
                loop = bpy_mesh.loops[loop_index]
                vert_index = loop.vertex_index
                uv = uvs[vert_index]
                rgb = lights['rgb'][vert_index]
                hemi = lights['hemi'][vert_index]
                sun = lights['sun'][vert_index]
                uv_layer.data[loop.index].uv = uv
                rgb_color.data[loop.index].color = rgb
                hemi_color.data[loop.index].color = (hemi, hemi, hemi, 1.0)
                sun_color.data[loop.index].color = (sun, sun, sun, 1.0)
    else:
        for face in bpy_mesh.polygons:
            for loop_index in face.loop_indices:
                loop = bpy_mesh.loops[loop_index]
                vert_index = loop.vertex_index
                uv = uvs[vert_index]
                rgb = lights['rgb'][vert_index]
                hemi = lights['hemi'][vert_index]
                sun = lights['sun'][vert_index]
                uv_layer.data[loop.index].uv = uv
                rgb_color.data[loop.index].color = rgb[0 : 3]
                hemi_color.data[loop.index].color = (hemi, hemi, hemi)
                sun_color.data[loop.index].color = (sun, sun, sun)
    bpy_object = create_object(visual.name, bpy_mesh)
    assign_material(bpy_object.data, visual, lvl)
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'LOD'
    return bpy_object


def import_tree_pm_visual(chunks, visual, lvl):
    visual.name = 'tree_pm'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, lvl)
    swi_index = import_swicontainer(chunks)
    if not bpy_mesh:
        swi = lvl.swis[swi_index]
        visual.indices = visual.indices[swi[0].offset : ]
        visual.indices_count = swi[0].triangles_count * 3
        convert_indices_to_triangles(visual)

        bpy_object = create_visual(visual, bpy_mesh, lvl, geometry_key)
    else:
        bpy_object = create_object(visual.name, bpy_mesh)
    tree_xform = import_tree_def_2(lvl, visual, chunks, bpy_object)
    set_tree_transforms(bpy_object, tree_xform)
    check_unread_chunks(chunks, context='TREE_PM_VISUAL')
    bpy_object.xray.is_level = True
    bpy_object.xray.level.object_type = 'VISUAL'
    bpy_object.xray.level.visual_type = 'TREE_PM'
    return bpy_object


def import_model_v4(chunks, visual, lvl):

    if visual.model_type == fmt.ModelType_v4.NORMAL:
        bpy_obj = import_normal_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v4.HIERRARHY:
        bpy_obj = import_hierrarhy_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v4.PROGRESSIVE:
        bpy_obj = import_progressive_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v4.TREE_ST:
        bpy_obj = import_tree_st_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v4.TREE_PM:
        bpy_obj = import_tree_pm_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v4.LOD:
        bpy_obj = import_lod_visual(chunks, visual, lvl)

    else:
        raise BaseException('unsupported model type: {:x}'.format(
            visual.model_type
        ))

    data = bpy_obj.xray
    data.is_ogf = True

    collection_name = level.create.LEVEL_VISUALS_COLLECTION_NAMES_TABLE[visual.name]
    collection = lvl.collections[collection_name]
    collection.objects.link(bpy_obj)
    if version_utils.IS_28:
        scene_collection = bpy.context.scene.collection
        scene_collection.objects.unlink(bpy_obj)
    lvl.visuals.append(bpy_obj)


def import_texture_and_shader_v3(visual, lvl, data):
    packed_reader = xray_io.PackedReader(data)
    visual.texture_id = packed_reader.getf('<I')[0]
    visual.shader_id = packed_reader.getf('<I')[0]


def import_model_v3(chunks, visual, lvl):
    chunks_ids = fmt.Chunks_v3
    if visual.model_type == fmt.ModelType_v3.NORMAL:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            import_texture_and_shader_v3(visual, lvl, texture_l_data)
        bpy_obj = import_normal_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.HIERRARHY:
        bpy_obj = import_hierrarhy_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.TREE:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            import_texture_and_shader_v3(visual, lvl, texture_l_data)
        bpy_obj = import_tree_st_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.LOD:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            import_texture_and_shader_v3(visual, lvl, texture_l_data)
        bpy_obj = import_lod_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.CACHED:
        texture_l_data = chunks.get(chunks_ids.TEXTURE_L)
        if texture_l_data:
            chunks.pop(chunks_ids.TEXTURE_L)
            import_texture_and_shader_v3(visual, lvl, texture_l_data)
        bpy_obj = import_normal_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v3.PROGRESSIVE2:
        ####################################################
        # DELETE
        ####################################################
        bpy_obj = bpy.data.objects.new('PROGRESSIVE2', None)
        bpy.context.scene.collection.objects.link(bpy_obj)
        visual.name = 'progressive'

    else:
        raise utils.AppError(
            text.error.ogf_bad_model_type,
            log.props(model_type=visual.model_type)
        )

    data = bpy_obj.xray
    data.is_ogf = True

    collection_name = level.create.LEVEL_VISUALS_COLLECTION_NAMES_TABLE[visual.name]
    collection = lvl.collections[collection_name]
    collection.objects.link(bpy_obj)
    if version_utils.IS_28:
        scene_collection = bpy.context.scene.collection
        scene_collection.objects.unlink(bpy_obj)
    lvl.visuals.append(bpy_obj)


def import_model_v2(chunks, visual, lvl):
    chunks_ids = fmt.Chunks_v2
    if visual.model_type == fmt.ModelType_v2.NORMAL:
        texture_l_data = chunks.pop(chunks_ids.TEXTURE_L)
        import_texture_and_shader_v3(visual, lvl, texture_l_data)
        bpy_obj = import_normal_visual(chunks, visual, lvl)

    elif visual.model_type == fmt.ModelType_v2.HIERRARHY:
        bpy_obj = import_hierrarhy_visual(chunks, visual, lvl)
    else:
        raise utils.AppError(
            text.error.ogf_bad_model_type,
            log.props(model_type=visual.model_type)
        )

    data = bpy_obj.xray
    data.is_ogf = True

    scene_collection = bpy.context.scene.collection
    collection_name = level.create.LEVEL_VISUALS_COLLECTION_NAMES_TABLE[visual.name]
    collection = lvl.collections[collection_name]
    collection.objects.link(bpy_obj)
    scene_collection.objects.unlink(bpy_obj)
    lvl.visuals.append(bpy_obj)


def import_bounding_sphere(packed_reader):
    center = packed_reader.getf('<3f')
    radius = packed_reader.getf('<f')[0]


def import_bounding_box(packed_reader):
    bbox_min = packed_reader.getf('<3f')
    bbox_max = packed_reader.getf('<3f')


def check_version(visual):
    if visual.format_version not in fmt.SUPPORT_FORMAT_VERSIONS:
        raise utils.AppError(
            text.error.ogf_bad_ver,
            log.props(version=visual.format_version)
        )


def import_header(data, visual):
    packed_reader = xray_io.PackedReader(data)
    visual.format_version = packed_reader.getf('<B')[0]
    check_version(visual)
    if visual.format_version == fmt.FORMAT_VERSION_4:
        visual.model_type = packed_reader.getf('<B')[0]
        visual.shader_id = packed_reader.getf('<H')[0]
        import_bounding_box(packed_reader)
        import_bounding_sphere(packed_reader)
    elif visual.format_version in (fmt.FORMAT_VERSION_3, fmt.FORMAT_VERSION_2):
        visual.model_type = packed_reader.getf('<B')[0]
        visual.shader_id = packed_reader.getf('<H')[0]


def import_main(chunks, visual, lvl):
    header_chunk_data = chunks.pop(fmt.HEADER)
    import_header(header_chunk_data, visual)

    # version 4
    if visual.format_version == fmt.FORMAT_VERSION_4:
        import_function = import_model_v4
        chunks_names = fmt.chunks_names_v4
        model_type_names = fmt.model_type_names_v4

    # version 3
    elif visual.format_version == fmt.FORMAT_VERSION_3:
        import_function = import_model_v3
        chunks_names = fmt.chunks_names_v3
        model_type_names = fmt.model_type_names_v3

    # version 2
    elif visual.format_version == fmt.FORMAT_VERSION_2:
        import_function = import_model_v2
        chunks_names = fmt.chunks_names_v2
        model_type_names = fmt.model_type_names_v2

    key = []
    for chunk_id in chunks.keys():
        key.append(chunks_names.get(
            chunk_id, 'UNKNOWN_{}'.format(hex(chunk_id))
            )
        )
    key.append('HEADER')
    key.sort()
    key.insert(0, model_type_names[visual.model_type])
    key = tuple(key)
    lvl.visual_keys.add(key)
    import_function(chunks, visual, lvl)


def get_ogf_chunks(data):
    chunked_reader = xray_io.ChunkedReader(data)
    del data
    chunks = {}
    chunks_ids = set()
    for chunk_id, chunkd_data in chunked_reader:
        chunks[chunk_id] = chunkd_data
        chunks_ids.add(hex(chunk_id))
    del chunked_reader
    return chunks, chunks_ids


def import_(data, visual_id, lvl, chunks, visuals_ids):
    chunks, visual_chunks_ids = get_ogf_chunks(data)
    visual = Visual()
    visual.visual_id = visual_id
    import_main(chunks, visual, lvl)


def import_description(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_DESC)
    packed_reader = xray_io.PackedReader(chunk_data)
    source_file = packed_reader.gets()
    build_name = packed_reader.gets()
    build_time = packed_reader.getf('<I')[0]
    visual.create_name = packed_reader.gets()
    visual.create_time = packed_reader.getf('<I')[0]
    visual.modif_name = packed_reader.gets()
    visual.modif_time = packed_reader.getf('<I')[0]


def import_bone_names(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_BONE_NAMES)
    packed_reader = xray_io.PackedReader(chunk_data)
    bones_count = packed_reader.getf('<I')[0]
    visual.bones = []
    for bone_index in range(bones_count):
        bone_name = packed_reader.gets()
        bone_parent = packed_reader.gets()
        rotation = packed_reader.getf('<9f')
        translation = packed_reader.getf('<3f')
        half_size = packed_reader.getf('<3f')
        visual.bones.append((bone_name, bone_parent))


def import_user_data(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_USERDATA, None)
    if not chunk_data:
        return
    packed_reader = xray_io.PackedReader(chunk_data)
    visual.user_data = packed_reader.gets(
        onerror=lambda e: log.warn(
            'bad userdata',
            error=str(e),
            file=visual.file_path
        )
    )


def import_ik_data(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_IKDATA, None)
    if not chunk_data:
        return
    packed_reader = xray_io.PackedReader(chunk_data)
    armature = bpy.data.armatures.new(name=visual.name)
    version_utils.set_arm_display_type(armature)
    arm_obj = bpy.data.objects.new(visual.name, armature)
    version_utils.set_object_show_xray(arm_obj, True)
    arm_obj.xray.isroot = True
    version_utils.link_object(arm_obj)
    version_utils.set_active_object(arm_obj)
    # motion references
    if visual.motion_refs:
        for motion_ref in visual.motion_refs:
            ref = arm_obj.xray.motionrefs_collection.add()
            ref.name = motion_ref
    revision = arm_obj.xray.revision
    revision.owner = visual.create_name
    revision.ctime = visual.create_time
    revision.moder = visual.modif_name
    revision.mtime = visual.modif_time
    if visual.user_data:
        arm_obj.xray.userdata = visual.user_data
    if visual.lod:
        arm_obj.xray.lodref = visual.lod
    bpy.ops.object.mode_set(mode='EDIT')
    bone_props = []
    armature_bones = {}
    for bone_index, (bone_name, parent_name) in enumerate(visual.bones):
        version = packed_reader.getf('<I')[0]
        props = []
        game_material = packed_reader.gets()
        shape_type = packed_reader.getf('<H')[0]
        shape_flags = packed_reader.getf('<H')[0]
        props.extend((
            game_material,
            shape_type,
            shape_flags
        ))
        # box shape
        box_shape_rotation = packed_reader.getf('<9f')
        box_shape_translation = packed_reader.getf('<3f')
        box_shape_half_size = packed_reader.getf('<3f')
        props.extend((
            box_shape_rotation,
            box_shape_translation,
            box_shape_half_size
        ))
        # sphere shape
        sphere_shape_translation = packed_reader.getf('<3f')
        sphere_shape_radius = packed_reader.getf('<f')[0]
        props.extend((
            sphere_shape_translation,
            sphere_shape_radius
        ))
        # cylinder shape
        cylinder_shape_translation = packed_reader.getf('<3f')
        cylinder_shape_direction = packed_reader.getf('<3f')
        cylinder_shape_height = packed_reader.getf('<f')[0]
        cylinder_shape_radius = packed_reader.getf('<f')[0]
        props.extend((
            cylinder_shape_translation,
            cylinder_shape_direction,
            cylinder_shape_height,
            cylinder_shape_radius
        ))

        joint_type = packed_reader.getf('<I')[0]
        props.append(joint_type)

        # x limits
        limit_x_min, limit_x_max = packed_reader.getf('<2f')
        limit_x_spring = packed_reader.getf('<f')[0]
        limit_x_damping = packed_reader.getf('<f')[0]
        props.extend((
            limit_x_min,
            limit_x_max,
            limit_x_spring,
            limit_x_damping
        ))
        # y limits
        limit_y_min, limit_y_max = packed_reader.getf('<2f')
        limit_y_spring = packed_reader.getf('<f')[0]
        limit_y_damping = packed_reader.getf('<f')[0]
        props.extend((
            limit_y_min,
            limit_y_max,
            limit_y_spring,
            limit_y_damping
        ))
        # z limits
        limit_z_min, limit_z_max = packed_reader.getf('<2f')
        limit_z_spring = packed_reader.getf('<f')[0]
        limit_z_damping = packed_reader.getf('<f')[0]
        props.extend((
            limit_z_min,
            limit_z_max,
            limit_z_spring,
            limit_z_damping
        ))

        joint_spring = packed_reader.getf('<f')[0]
        joint_damping = packed_reader.getf('<f')[0]
        ik_flags = packed_reader.getf('<I')[0]
        breakable_force = packed_reader.getf('<f')[0]
        breakable_torque = packed_reader.getf('<f')[0]
        friction = packed_reader.getf('<f')[0]
        props.extend((
            joint_spring,
            joint_damping,
            ik_flags,
            breakable_force,
            breakable_torque,
            friction
        ))

        # bind pose
        bind_rotation = packed_reader.getv3f()
        bind_translation = packed_reader.getv3f()

        # mass
        mass_value = packed_reader.getf('<f')[0]
        mass_center = packed_reader.getv3f()
        props.extend((
            mass_value,
            mass_center,
        ))

        bone_props.append(props)

        # create bone
        bpy_bone = armature.edit_bones.new(name=bone_name)
        armature_bones[bone_index] = bpy_bone.name
        rotation = mathutils.Euler(
            (-bind_rotation[0], -bind_rotation[1], -bind_rotation[2]), 'YXZ'
        ).to_matrix().to_4x4()
        translation = mathutils.Matrix.Translation(bind_translation)
        mat = version_utils.multiply(
            translation,
            rotation,
            xray_motions.MATRIX_BONE
        )
        if parent_name:
            bpy_bone.parent = armature.edit_bones.get(parent_name, None)
            if bpy_bone.parent:
                mat = version_utils.multiply(
                    bpy_bone.parent.matrix,
                    xray_motions.MATRIX_BONE_INVERTED,
                    mat
                )
            else:
                log.warn(
                    text.warn.no_bone_parent,
                    bone=bone_name,
                    parent=parent_name
                )
        bpy_bone.tail.y = 0.02
        bpy_bone.matrix = mat

    bpy.ops.object.mode_set(mode='OBJECT')

    for bone_index, props in enumerate(bone_props):
        bone_name = armature_bones[bone_index]
        bone = armature.bones[bone_name]
        xray = bone.xray
        shape = xray.shape
        ik = xray.ikjoint
        shape.set_curver()
        i = 0
        xray.gamemtl = props[i]
        i += 1
        if props[i] <= 3:
            shape.type = str(props[i])
        else:
            log.warn(
                text.warn.ogf_bad_shape,
                file=visual.file_path,
                bone=bone.name
            )
        i += 1
        shape.flags = props[i]
        i += 1
        shape.box_rot = props[i]
        i += 1
        shape.box_trn = props[i]
        i += 1
        shape.box_hsz = props[i]
        i += 1
        shape.sph_pos = props[i]
        i += 1
        shape.sph_rad = props[i]
        i += 1
        shape.cyl_pos = props[i]
        i += 1
        shape.cyl_dir = props[i]
        i += 1
        shape.cyl_hgh = props[i]
        i += 1
        shape.cyl_rad = props[i]
        i += 1
        if props[i] <= 5:
            ik.type = str(props[i])
        else:
            log.warn(
                text.warn.ogf_bad_joint,
                file=visual.file_path,
                bone=bone.name
            )
        i += 1
        ik.lim_x_max = -props[i]
        i += 1
        ik.lim_x_min = -props[i]
        i += 1
        ik.lim_x_spr = props[i]
        i += 1
        ik.lim_x_dmp = props[i]
        i += 1
        ik.lim_y_max = -props[i]
        i += 1
        ik.lim_y_min = -props[i]
        i += 1
        ik.lim_y_spr = props[i]
        i += 1
        ik.lim_y_dmp = props[i]
        i += 1
        ik.lim_z_max = -props[i]
        i += 1
        ik.lim_z_min = -props[i]
        i += 1
        ik.lim_z_spr = props[i]
        i += 1
        ik.lim_z_dmp = props[i]
        i += 1
        ik.spring = props[i]
        i += 1
        ik.damping = props[i]
        i += 1
        xray.ikflags = props[i]
        i += 1
        xray.breakf.force = props[i]
        i += 1
        xray.breakf.torque = props[i]
        i += 1
        xray.friction = props[i]
        i += 1
        xray.mass.value = props[i]
        i += 1
        xray.mass.center = props[i]

    for bone in arm_obj.pose.bones:
        bone.rotation_mode = 'ZXY'
    visual.arm_obj = arm_obj


def import_children(context, chunks, ogf_chunks, root_visual):
    chunk_data = chunks.pop(ogf_chunks.CHILDREN, None)
    if not chunk_data:
        return
    chunked_reader = xray_io.ChunkedReader(chunk_data)
    for child_index, child_data in chunked_reader:
        visual = Visual()
        visual.file_path = root_visual.file_path
        visual.name = root_visual.name + ' {:0>2}'.format(child_index)
        visual.visual_id = child_index
        visual.is_root = False
        visual.arm_obj = root_visual.arm_obj
        visual.root_obj = root_visual.root_obj
        visual.bones = root_visual.bones
        visual.bpy_materials = root_visual.bpy_materials
        import_visual(context, child_data, visual)
        if visual.model_type == fmt.ModelType_v4.SKELETON_GEOMDEF_PM:
            root_visual.arm_obj.xray.flags_simple = 'pd'
        elif visual.model_type == fmt.ModelType_v4.SKELETON_GEOMDEF_ST:
            root_visual.arm_obj.xray.flags_simple = 'dy'
        elif visual.model_type == fmt.ModelType_v4.PROGRESSIVE:
            root_visual.root_obj.xray.flags_simple = 'pd'
        elif visual.model_type == fmt.ModelType_v4.NORMAL:
            root_visual.root_obj.xray.flags_simple = 'dy'
        else:
            print('WARRNING: Model type = {}'.format(visual.model_type))


def import_lods(context, chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_LODS, None)
    if not chunk_data:
        return
    packed_reader = xray_io.PackedReader(chunk_data)
    lod = packed_reader.gets()
    if lod.endswith('\r\n'):
        lod = lod[ : -2]
    visual.lod = lod


def import_mt_skeleton_rigid(context, chunks, ogf_chunks, visual):
    import_description(chunks, ogf_chunks, visual)
    import_bone_names(chunks, ogf_chunks, visual)
    import_lods(context, chunks, ogf_chunks, visual)
    import_ik_data(chunks, ogf_chunks, visual)
    import_children(context, chunks, ogf_chunks, visual)


def import_mt_hierrarhy(context, chunks, ogf_chunks, visual):
    import_description(chunks, ogf_chunks, visual)
    import_children(context, chunks, ogf_chunks, visual)


def import_texture(context, chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.TEXTURE)
    packed_reader = xray_io.PackedReader(chunk_data)
    texture = packed_reader.gets()
    shader = packed_reader.gets()
    bpy_material = create.material.get_material(
        context,
        texture,    # material name
        texture,
        shader,
        'default',    # compile shader
        'default_object',    # game material
        0,    # two sided flag
        'Texture'    # uv map name
    )
    visual.bpy_materials[visual.shader_id] = bpy_material


def import_swi(visual, chunks):
    swi = import_swidata(chunks)
    visual.indices = visual.indices[swi[0].offset : ]
    visual.indices_count = swi[0].triangles_count * 3


def import_mt_skeleton_geom_def_st(context, chunks, ogf_chunks, visual):
    import_texture(context, chunks, ogf_chunks, visual)
    import_skeleton_vertices(chunks, ogf_chunks, visual)
    import_indices(chunks, ogf_chunks, visual)


def import_mt_skeleton_geom_def_pm(context, chunks, ogf_chunks, visual):
    import_mt_skeleton_geom_def_st(context, chunks, ogf_chunks, visual)
    import_swi(visual, chunks)


def import_mt_normal(context, chunks, ogf_chunks, visual):
    import_texture(context, chunks, ogf_chunks, visual)
    import_vertices(chunks, ogf_chunks, visual)
    import_indices(chunks, ogf_chunks, visual)


def import_mt_progressive(context, chunks, ogf_chunks, visual):
    import_mt_normal(context, chunks, ogf_chunks, visual)
    import_swi(visual, chunks)


def read_motion_references(chunks, ogf_chunks, visual):
    data = chunks.pop(ogf_chunks.S_MOTION_REFS_0, None)
    if not data:
        data = chunks.pop(ogf_chunks.S_MOTION_REFS_2, None)
        if data:
            packed_reader = xray_io.PackedReader(data)
            count = packed_reader.getf('<I')[0]
            refs = []
            for index in range(count):
                ref = packed_reader.gets()
                refs.append(ref)
            visual.motion_refs = refs
    else:
        packed_reader = xray_io.PackedReader(data)
        visual.motion_refs = packed_reader.gets().split(',')


def import_mt_skeleton_anim(context, chunks, ogf_chunks, visual):
    read_motion_references(chunks, ogf_chunks, visual)
    import_mt_skeleton_rigid(context, chunks, ogf_chunks, visual)
    if context.import_motions:
        motions_data = chunks.pop(ogf_chunks.S_MOTIONS, None)
        params_data = chunks.pop(ogf_chunks.S_SMPARAMS, None)
        if params_data and motions_data:
            context.bpy_arm_obj = visual.arm_obj
            motions_params, bone_names = omf.imp.read_params(params_data, context)
            omf.imp.read_motions(motions_data, context, motions_params, bone_names)


def import_visual(context, data, visual):
    chunks, visual_chunks_ids = get_ogf_chunks(data)
    header_chunk_data = chunks.pop(fmt.HEADER)
    import_header(header_chunk_data, visual)
    if visual.format_version != fmt.FORMAT_VERSION_4:
        raise utils.AppError(
            text.error.ogf_bad_ver,
            log.props(version=visual.format_version)
        )
    ogf_chunks = fmt.Chunks_v4
    model_types = fmt.ModelType_v4
    import_user_data(chunks, ogf_chunks, visual)
    if visual.model_type == model_types.SKELETON_RIGID:
        import_mt_skeleton_rigid(context, chunks, ogf_chunks, visual)
    elif visual.model_type == model_types.SKELETON_ANIM:
        import_mt_skeleton_anim(context, chunks, ogf_chunks, visual)
    elif visual.model_type == model_types.SKELETON_GEOMDEF_ST:
        import_mt_skeleton_geom_def_st(context, chunks, ogf_chunks, visual)
    elif visual.model_type == model_types.SKELETON_GEOMDEF_PM:
        import_mt_skeleton_geom_def_pm(context, chunks, ogf_chunks, visual)
    elif visual.model_type == model_types.NORMAL:
        import_mt_normal(context, chunks, ogf_chunks, visual)
    elif visual.model_type == model_types.PROGRESSIVE:
        import_mt_progressive(context, chunks, ogf_chunks, visual)
    elif visual.model_type == model_types.HIERRARHY:
        root_obj = bpy.data.objects.new(visual.name, None)
        root_obj.xray.version = context.version
        root_obj.xray.isroot = True
        version_utils.link_object(root_obj)
        visual.root_obj = root_obj
        import_mt_hierrarhy(context, chunks, ogf_chunks, visual)
    else:
        raise utils.AppError(
            text.error.ogf_bad_model_type,
            log.props(model_type=visual.model_type)
        )
    for chunk_id, chunk_data in chunks.items():
        print('Unknown OGF chunk: {}, size: {}'.format(
            hex(chunk_id), len(chunk_data)
        ))
    if not visual.is_root:
        convert_indices_to_triangles(visual)
        bpy_object = create_visual(visual)
        arm = visual.arm_obj
        if arm:
            bpy_object.parent = arm
            mod = bpy_object.modifiers.new('Armature', 'ARMATURE')
            mod.object = arm
            bpy_object.xray.isroot = False
        elif visual.root_obj:
            bpy_object.parent = visual.root_obj
            bpy_object.xray.version = context.version
            bpy_object.xray.isroot = False
    elif visual.model_type in (model_types.NORMAL, model_types.PROGRESSIVE):
        convert_indices_to_triangles(visual)
        bpy_object = create_visual(visual)


@log.with_context(name='file')
def import_file(context, file_path, file_name):
    log.update(path=file_path)
    ie_utils.check_file_exists(file_path)
    data = utils.read_file(file_path)
    visual = Visual()
    visual.file_path = file_path
    visual.visual_id = 0
    visual.name = file_name
    visual.is_root = True
    visual.bpy_materials = {}
    import_visual(context, data, visual)
