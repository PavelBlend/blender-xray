# addon modules
from .. import fmt
from ... import level
from .... import rw
from .... import text
from .... import log


def read_vertices_v3(data, visual, lvl):
    packed_reader = rw.read.PackedReader(data)

    vb = level.imp.vb.import_vertex_buffer_d3d7(packed_reader, lvl.xrlc_version)

    visual.vertices = vb.position
    visual.normals = vb.normal
    visual.uvs = vb.uv
    visual.uvs_lmap = vb.uv_lmap


def read_verts_1_link(visual, packed_reader, verices_count):
    if verices_count * 36 == packed_reader.get_size() - 8:
        for vertex_index in range(verices_count):
            coord = packed_reader.getv3fp()
            normal = packed_reader.getv3fp()
            tex_u, tex_v = packed_reader.getf('<2f')
            bone_index = packed_reader.uint32()

            vertex_weights = [(bone_index, 1), ]

            visual.vertices.append(coord)
            visual.normals.append(normal)
            visual.uvs.append((tex_u, 1 - tex_v))
            visual.weights.append(vertex_weights)
            visual.deform_bones.add(bone_index)

    else:
        for vertex_index in range(verices_count):
            coord = packed_reader.getv3fp()
            normal = packed_reader.getv3fp()
            tangent = packed_reader.getv3fp()
            bitangent = packed_reader.getv3fp()
            tex_u, tex_v = packed_reader.getf('<2f')
            bone_index = packed_reader.uint32()

            vertex_weights = [(bone_index, 1), ]

            visual.vertices.append(coord)
            visual.normals.append(normal)
            visual.uvs.append((tex_u, 1 - tex_v))
            visual.weights.append(vertex_weights)
            visual.deform_bones.add(bone_index)


def read_verts_2_link(visual, packed_reader, verices_count):
    for vertex_index in range(verices_count):
        bone_1_index, bone_2_index = packed_reader.getf('<2H')
        coord = packed_reader.getv3fp()
        normal = packed_reader.getv3fp()
        tangent = packed_reader.getv3fp()
        bitangent = packed_reader.getv3fp()
        weight = packed_reader.getf('<f')[0]
        tex_u, tex_v = packed_reader.getf('<2f')

        if bone_1_index != bone_2_index:
            vertex_weights = [
                (bone_1_index, 1 - weight),
                (bone_2_index, weight)
            ]
        else:
            vertex_weights = [(bone_1_index, 1), ]

        visual.vertices.append(coord)
        visual.normals.append(normal)
        visual.uvs.append((tex_u, 1 - tex_v))
        visual.weights.append(vertex_weights)
        visual.deform_bones.update((bone_1_index, bone_2_index))


def read_verts_3_link(visual, packed_reader, verices_count):
    for vertex_index in range(verices_count):
        bone_indices = packed_reader.getf('<3H')
        coord = packed_reader.getv3fp()
        normal = packed_reader.getv3fp()
        tangent = packed_reader.getv3fp()
        bitangent = packed_reader.getv3fp()
        weight_1, weight_2 = packed_reader.getf('<2f')
        tex_u, tex_v = packed_reader.getf('<2f')

        weight_3 = 1 - weight_1 - weight_2

        vertex_weights = []
        bone_weights = [weight_1, weight_2, weight_3]
        used_bones = []
        for bone, weight in zip(bone_indices, bone_weights):
            if bone in used_bones:
                continue
            used_bones.append(bone)
            vertex_weights.append((bone, weight))

        visual.vertices.append(coord)
        visual.normals.append(normal)
        visual.uvs.append((tex_u, 1 - tex_v))
        visual.weights.append(vertex_weights)
        visual.deform_bones.update(bone_indices)


def read_verts_4_link(visual, packed_reader, verices_count):
    for vertex_index in range(verices_count):
        bone_indices = packed_reader.getf('<4H')
        coord = packed_reader.getv3fp()
        normal = packed_reader.getv3fp()
        tangent = packed_reader.getv3fp()
        bitangent = packed_reader.getv3fp()
        weight_1, weight_2, weight_3 = packed_reader.getf('<3f')
        tex_u, tex_v = packed_reader.getf('<2f')

        weight_4 = 1 - weight_1 - weight_2 - weight_3

        bone_weights = (weight_1, weight_2, weight_3, weight_4)
        used_bones = []
        vertex_weights = []
        for bone, weight in zip(bone_indices, bone_weights):
            if bone in used_bones:
                continue
            used_bones.append(bone)
            vertex_weights.append((bone, weight))

        visual.vertices.append(coord)
        visual.normals.append(normal)
        visual.uvs.append((tex_u, 1 - tex_v))
        visual.weights.append(vertex_weights)
        visual.deform_bones.update(bone_indices)


def read_skeleton_vertices(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.VERTICES)
    packed_reader = rw.read.PackedReader(chunk_data)

    vert_fmt = packed_reader.uint32()
    verices_count = packed_reader.uint32()

    visual.deform_bones = set()

    if vert_fmt in (fmt.VertexFormat.FVF_1L, fmt.VertexFormat.FVF_1L_CS):
        read_verts_1_link(visual, packed_reader, verices_count)

    elif vert_fmt in (fmt.VertexFormat.FVF_2L, fmt.VertexFormat.FVF_2L_CS):
        read_verts_2_link(visual, packed_reader, verices_count)

    elif vert_fmt == fmt.VertexFormat.FVF_3L_CS:
        read_verts_3_link(visual, packed_reader, verices_count)

    elif vert_fmt == fmt.VertexFormat.FVF_4L_CS:
        read_verts_4_link(visual, packed_reader, verices_count)

    else:
        raise log.AppError(
            text.error.ogf_bad_vertex_fmt,
            log.props(vertex_format=hex(vert_fmt))
        )


def read_vertices(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.VERTICES)
    packed_reader = rw.read.PackedReader(chunk_data)

    vert_fmt = packed_reader.uint32()
    vertices_count = packed_reader.uint32()

    if vert_fmt == fmt.VertexFormat.FVF_OGF:
        for vertex_index in range(vertices_count):
            coord = packed_reader.getv3fp()
            normal = packed_reader.getv3fp()
            tex_u, tex_v = packed_reader.getf('<2f')

            visual.vertices.append(coord)
            visual.normals.append(normal)
            visual.uvs.append((tex_u, 1 - tex_v))

    else:
        raise log.AppError(
            text.error.ogf_bad_vertex_fmt,
            log.props(vertex_format=vert_fmt)
        )
        
def read_skeleton_vertices_build_375(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.VERTICES_B375)
    packed_reader = rw.read.PackedReader(chunk_data)
    
    num_used_bones = packed_reader.byte()
    bones_remap = packed_reader.get_array('B', num_used_bones)

    vertices_count = packed_reader.uint32()
    
    visual.deform_bones = set()

    for vertex_index in range(vertices_count):
        packed_coord = packed_reader.getf('<3h')
        dummy = packed_reader.getf('<H') # num of bones with weight >0 ?
        packed_normal_ao = packed_reader.getf('<4B')
        packed_tangent = packed_reader.getf('<4B')
        packed_binormal = packed_reader.getf('<4B')
        bone_ids = packed_reader.getf('<4B') # points to bones_remap, each index is multiplied by 3
        bone_weights = packed_reader.getf('<4B')
        packed_tc = packed_reader.getf('<2h')
        
        pX = packed_coord[0] / 2720
        pY = packed_coord[1] / 2720
        pZ = packed_coord[2] / 2720
        
        nX = packed_normal_ao[2] / 255 * 2 - 1
        nY = packed_normal_ao[1] / 255 * 2 - 1
        nZ = packed_normal_ao[0] / 255 * 2 - 1
        
        tex_u = packed_tc[0] / 2048
        tex_v = packed_tc[1] / 2048
        
        bone1 = bones_remap[bone_ids[0] // 3][0]
        bone2 = bones_remap[bone_ids[1] // 3][0]
        bone3 = bones_remap[bone_ids[2] // 3][0]
        bone4 = bones_remap[bone_ids[3] // 3][0]
        
        bone_indices = (bone1, bone2, bone3, bone4)
        bone_weights = (bone_weights[0] / 255, bone_weights[1] / 255, bone_weights[2] / 255, bone_weights[3] / 255)
        
        used_bones = []
        vertex_weights = []
        for bone, weight in zip(bone_indices, bone_weights):
            if bone in used_bones:
                continue
            used_bones.append(bone)
            vertex_weights.append((bone, weight))

        visual.vertices.append((pX, pZ, pY))
        visual.normals.append((nX, nZ, nY))
        visual.uvs.append((tex_u, 1 - tex_v))
        visual.weights.append(vertex_weights)
        visual.deform_bones.update(bone_indices)

