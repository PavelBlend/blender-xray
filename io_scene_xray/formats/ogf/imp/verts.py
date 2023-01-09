# addon modules
from .. import fmt
from ... import level
from .... import rw
from .... import text
from .... import log


def read_vertices_v3(data, visual, lvl):
    packed_reader = rw.read.PackedReader(data)
    vb = level.vb.import_vertex_buffer_d3d7(packed_reader, lvl)
    visual.vertices = vb.position
    visual.normals = vb.normal
    visual.uvs = vb.uv
    visual.uvs_lmap = vb.uv_lmap


def import_skeleton_vertices(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.VERTICES)
    packed_reader = rw.read.PackedReader(chunk_data)
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
            normal = packed_reader.getv3fp()
            tangent = packed_reader.getv3fp()
            bitangent = packed_reader.getv3fp()
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
            normal = packed_reader.getv3fp()
            tangent = packed_reader.getv3fp()
            bitangent = packed_reader.getv3fp()
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
            normal = packed_reader.getv3fp()
            tangent = packed_reader.getv3fp()
            bitangent = packed_reader.getv3fp()
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
            normal = packed_reader.getv3fp()
            tangent = packed_reader.getv3fp()
            bitangent = packed_reader.getv3fp()
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
        raise log.AppError(
            text.error.ogf_bad_vertex_fmt,
            log.props(vertex_format=hex(vertex_format))
        )
    visual.vertices = vertices
    visual.normals = normals
    visual.uvs = uvs
    visual.weights = weights


def import_vertices(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.VERTICES)
    packed_reader = rw.read.PackedReader(chunk_data)
    vertex_format = packed_reader.getf('<I')[0]
    verices_count = packed_reader.getf('<I')[0]
    vertices = []
    normals = []
    uvs = []
    if vertex_format == level.fmt.FVF_OGF:
        for vertex_index in range(verices_count):
            coords = packed_reader.getv3f()
            normal = packed_reader.getv3fp()
            tex_u, tex_v = packed_reader.getf('<2f')
            vertices.append(coords)
            normals.append(normal)
            uvs.append((tex_u, 1 - tex_v))
    else:
        raise log.AppError(
            text.error.ogf_bad_vertex_fmt,
            log.props(vertex_format=vertex_format)
        )
    visual.vertices = vertices
    visual.normals = normals
    visual.uvs = uvs
