# blender modules
import bmesh

# addon modules
from . import main
from .. import fmt
from ... import text
from ... import xray_io
from ... import utils
from ... import log
from ... import version_utils


def _export_sg_cs_cop(bmfaces):
    for face in bmfaces:
        sm_group = 0
        for eidx, edge in enumerate(face.edges):
            if not edge.smooth:
                sm_group |= (4, 2, 1)[eidx]
        yield sm_group


def _check_sg_soc(bmedges, sgroups):
    for edge in bmedges:
        if len(edge.link_faces) != 2:
            continue
        sg0 = sgroups[edge.link_faces[0].index]
        sg1 = sgroups[edge.link_faces[1].index]
        if edge.smooth:
            if sg0 != sg1:
                return text.warn.object_sg_smooth
        else:
            if sg0 == sg1:
                return text.warn.object_sg_sharp


def _mark_fsg(face, sgroup, face_sgroup):
    faces = [face]
    for face in faces:
        for edge in face.edges:
            if not edge.smooth:
                continue
            for linked_face in edge.link_faces:
                if face_sgroup.get(linked_face) is None:
                    face_sgroup[linked_face] = sgroup
                    faces.append(linked_face)


def _export_sg_soc(bmfaces):
    face_sgroup = dict()
    sgroup_gen = 0
    for face in bmfaces:
        sgroup = face_sgroup.get(face)
        if sgroup is None:
            face_sgroup[face] = sgroup = sgroup_gen
            sgroup_gen += 1
            _mark_fsg(face, sgroup, face_sgroup)
        yield sgroup


def export_version(cw):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<H', fmt.CURRENT_MESH_VERSION)
    cw.put(fmt.Chunks.Mesh.VERSION, packed_writer)


def export_mesh_name(chunked_writer, bpy_obj, bpy_root):
    if bpy_obj == bpy_root:
        mesh_name = bpy_obj.data.name
    else:
        mesh_name = bpy_obj.name
    packed_writer = xray_io.PackedWriter()
    packed_writer.puts(mesh_name)
    chunked_writer.put(fmt.Chunks.Mesh.MESHNAME, packed_writer)


def export_bbox(chunked_writer, bm):
    bbox = utils.calculate_mesh_bbox(bm.verts)
    packed_writer = xray_io.PackedWriter()
    packed_writer.putv3f(bbox[0])
    packed_writer.putv3f(bbox[1])
    chunked_writer.put(fmt.Chunks.Mesh.BBOX, packed_writer)


def export_flags(chunked_writer, bpy_obj):
    if hasattr(bpy_obj.data, 'xray'):
        # MAX sg-format currently unsupported (we use Maya sg-format)
        flags = bpy_obj.data.xray.flags & ~fmt.Chunks.Mesh.Flags.SG_MASK
    else:
        flags = fmt.Chunks.Mesh.Flags.VISIBLE
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<B', flags)
    chunked_writer.put(fmt.Chunks.Mesh.FLAGS, packed_writer)


def remove_bad_geometry(bm, bml, bpy_obj):
    bad_vgroups = [
        (vertex_group.name.startswith(utils.BAD_VTX_GROUP_NAME), vertex_group.name) \
        for vertex_group in bpy_obj.vertex_groups
    ]
    bad_verts = [
        vertex for vertex in bm.verts
        if any(bad_vgroups[key][0] for key in vertex[bml].keys())
    ]
    if bad_verts:
        for is_bad, vgroup_name in bad_vgroups:
            if is_bad:
                log.warn(
                    text.warn.object_skip_geom,
                    vertex_group=vgroup_name,
                    object=bpy_obj.name
                )
        if version_utils.IS_28:
            ops_context = 'VERTS'
        else:
            ops_context = 1
        bmesh.ops.delete(bm, geom=bad_verts, context=ops_context)

    return bad_vgroups


def export_vertices(chunked_writer, bm):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', len(bm.verts))
    for vertex in bm.verts:
        packed_writer.putv3f(vertex.co)
    chunked_writer.put(fmt.Chunks.Mesh.VERTS, packed_writer)


def export_faces(chunked_writer, bm, bpy_obj):
    uvs = []
    vert_indices = []
    face_indices = []
    uv_layer = bm.loops.layers.uv.active
    if not uv_layer:
        raise utils.AppError(
            text.error.object_no_uv,
            log.props(object=bpy_obj.name)
        )

    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', len(bm.faces))
    for face in bm.faces:
        for vert_index in (0, 2, 1):
            packed_writer.putf('<2I', face.verts[vert_index].index, len(uvs))
            uv_coord = face.loops[vert_index][uv_layer].uv
            uvs.append((uv_coord[0], 1 - uv_coord[1]))
            vert_indices.append(face.verts[vert_index].index)
            face_indices.append(face.index)
    chunked_writer.put(fmt.Chunks.Mesh.FACES, packed_writer)

    return uvs, vert_indices, face_indices


@log.with_context('mesh')
def export_mesh(bpy_obj, bpy_root, chunked_writer, context):
    log.update(mesh=bpy_obj.data.name)
    export_version(chunked_writer)
    export_mesh_name(chunked_writer, bpy_obj, bpy_root)

    if context.smoothing_out_of == 'SHARP_EDGES':
        use_split_normals = False
    else:
        use_split_normals = True

    modifiers = [
        mod
        for mod in bpy_obj.modifiers
            if mod.type != 'ARMATURE' and mod.show_viewport
    ]

    bm = utils.convert_object_to_space_bmesh(
        bpy_obj,
        bpy_root.matrix_world,
        local=False,
        split_normals=use_split_normals,
        mods=modifiers
    )

    weights_layer = bm.verts.layers.deform.verify()
    bad_vgroups = remove_bad_geometry(bm, weights_layer, bpy_obj)

    export_bbox(chunked_writer, bm)
    export_flags(chunked_writer, bpy_obj)

    bmesh.ops.triangulate(bm, faces=bm.faces)

    export_vertices(chunked_writer, bm)

    uvs, vert_indices, face_indices = export_faces(chunked_writer, bm, bpy_obj)

    if bpy_root.type == 'ARMATURE':
        bones_names = []
        for bone in bpy_root.data.bones:
            if bone.xray.exportable:
                bones_names.append(bone.name)
    else:
        bones_names = None

    weight_maps = []
    weight_maps_count = 0
    for vertex_group, (is_bad, _) in zip(bpy_obj.vertex_groups, bad_vgroups):
        if is_bad:
            weight_maps.append(None)
            continue
        if not bones_names is None:
            if vertex_group.name not in bones_names:
                weight_maps.append(None)
                continue
        weight_maps.append(([], weight_maps_count))
        weight_maps_count += 1

    weight_refs = []    # vertex weight references
    for vertex_index, vertex in enumerate(bm.verts):
        weight_ref = []
        weight_refs.append(weight_ref)
        vertex_weights = vertex[weights_layer]
        for vertex_group_index in vertex_weights.keys():
            weight_map = weight_maps[vertex_group_index]
            if weight_map is None:
                continue
            weight_ref.append((
                1 + weight_map[1],
                len(weight_map[0])
            ))
            weight_map[0].append(vertex_index)

    # vertex map references chunk
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', len(uvs))
    uv_maps_count = 1
    uv_map_index = 0
    for vertex_map_index in range(len(uvs)):
        vertex_index = vert_indices[vertex_map_index]
        weight_ref = weight_refs[vertex_index]
        # vertex references count
        refs_count = uv_maps_count + len(weight_ref)
        packed_writer.putf('<B', refs_count)
        # uv ref
        packed_writer.putf('<2I', uv_map_index, vertex_map_index)
        # weight refs
        for ref in weight_ref:
            packed_writer.putf('<2I', *ref)
    chunked_writer.put(fmt.Chunks.Mesh.VMREFS, packed_writer)

    packed_writer = xray_io.PackedWriter()
    face_materials = {
        (material.name, material_index)
        if material else (None, material_index): [
            face_index
            for face_index, face in enumerate(bm.faces)
                if face.material_index == material_index
        ]
        for material_index, material in enumerate(bpy_obj.data.materials)
    }

    materials = {}
    for (material_name, material_index), faces_indices in face_materials.items():
        mat = materials.setdefault(
            material_name,
            {
                'materials_ids': [],
                'faces_count': []
            }
        )
        mat['materials_ids'].append(material_index)
        mat['faces_count'].append(len(faces_indices))

    used_material_names = set()
    for (material_name, material_index), faces_indices in face_materials.items():
        if faces_indices:
            if material_name is None:
                raise utils.AppError(
                    text.error.obj_empty_mat,
                    log.props(object=bpy_obj.name)
                )
            used_material_names.add(material_name)

    if not face_materials:
        raise utils.AppError(
            text.error.obj_no_mat,
            log.props(object=bpy_obj.name)
        )

    # sface chunk
    packed_writer.putf('<H', len(used_material_names))
    for mat_name, mat_data in materials.items():
        if mat_name in used_material_names:
            faces_count = sum(mat_data['faces_count'])
            packed_writer.puts(mat_name)
            packed_writer.putf('<I', faces_count)
            for mat_id in mat_data['materials_ids']:
                material_face_indices = face_materials[(mat_name, mat_id)]
                for face_index in material_face_indices:
                    packed_writer.putf('<I', face_index)
    chunked_writer.put(fmt.Chunks.Mesh.SFACE, packed_writer)

    # smothing groups chunk
    packed_writer = xray_io.PackedWriter()
    smooth_groups = []
    if context.soc_sgroups:
        smooth_groups = tuple(_export_sg_soc(bm.faces))
        # check for Maya compatibility
        err = _check_sg_soc(bm.edges, smooth_groups)
        if err:
            log.warn(err, object=bpy_obj.name, mesh=bpy_obj.data.name)
    else:
        smooth_groups = _export_sg_cs_cop(bm.faces)
    for smooth_group in smooth_groups:
        packed_writer.putf('<I', smooth_group)
    chunked_writer.put(fmt.Chunks.Mesh.SG, packed_writer)

    # write vmaps chunk
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('<I', uv_maps_count + weight_maps_count)
    if version_utils.IS_28:
        texture = bpy_obj.data.uv_layers.active
    else:
        texture = bpy_obj.data.uv_textures.active
    packed_writer.puts(texture.name)
    packed_writer.putf('<B', 2)    # dim
    packed_writer.putf('<B', 1)    # discon
    packed_writer.putf('<B', fmt.VMapTypes.UVS)    # type
    packed_writer.putf('<I', len(uvs))
    # write uv coords
    for uvc in uvs:
        packed_writer.putf('<2f', *uvc)
    for vidx in vert_indices:
        packed_writer.putf('<I', vidx)
    for fidx in face_indices:
        packed_writer.putf('<I', fidx)
    # write vertex weights
    for group_index, vertex_group in enumerate(bpy_obj.vertex_groups):
        weight_map = weight_maps[group_index]
        if weight_map is None:
            continue
        vert_indices = weight_map[0]
        packed_writer.puts(vertex_group.name.lower())
        packed_writer.putf('<B', 1)    # dim
        packed_writer.putf('<B', 0)    # discon
        packed_writer.putf('<B', fmt.VMapTypes.WEIGHTS)    # type
        packed_writer.putf('<I', len(vert_indices))
        for vert_index in vert_indices:
            packed_writer.putf('<f', bm.verts[vert_index][weights_layer][group_index])
        packed_writer.putf('<' + str(len(vert_indices)) + 'I', *vert_indices)
    chunked_writer.put(fmt.Chunks.Mesh.VMAPS2, packed_writer)

    return used_material_names
