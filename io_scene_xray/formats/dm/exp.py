# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import fmt
from . import validate
from ... import utils
from ... import log
from ... import text
from ... import rw


def export(
        bpy_obj,
        packed_writer,
        context,
        file_path,
        mode='DM',
        warn_list=None
    ):
    if mode == 'DM':
        file_path = None    # level folder not use

    bpy_material, tex_name = validate.validate_export_object(
        context,
        bpy_obj,
        file_path,
        warn_list
    )

    det_model = bpy_obj.xray.detail.model
    packed_writer.puts(bpy_material.xray.eshader)
    packed_writer.puts(tex_name)
    packed_writer.putf('<I', int(det_model.no_waving))
    packed_writer.putf('<2f', det_model.min_scale, det_model.max_scale)

    if mode == 'DM':
        b_mesh = utils.mesh.convert_object_to_space_bmesh(
            bpy_obj,
            mathutils.Matrix.Identity(4),
            mathutils.Matrix.Identity(4),
            mathutils.Vector((1.0, 1.0, 1.0))
        )

    else:
        loc_mat, rot_mat = utils.ie.get_object_transform_matrix(bpy_obj)
        b_mesh = utils.mesh.convert_object_to_space_bmesh(
            bpy_obj,
            loc_mat,
            mathutils.Matrix.Identity(4),
            bpy_obj.scale
        )

    bmesh.ops.triangulate(b_mesh, faces=b_mesh.faces)
    bpy_data = bpy.data.meshes.new('.export-dm')
    b_mesh.to_mesh(bpy_data)
    bml_uv = b_mesh.loops.layers.uv.active
    vertices = []
    indices = []
    vmap = {}

    for face in b_mesh.faces:
        _ = []
        for loop in face.loops:
            uv = loop[bml_uv].uv
            vtx = (loop.vert.co.to_tuple(), (uv[0], 1 - uv[1]))
            vi = vmap.get(vtx)
            if vi is None:
                vmap[vtx] = vi = len(vertices)
                vertices.append(vtx)
            _.append(vi)
        indices.append(_)

    vertices_count = len(vertices)
    if vertices_count > fmt.VERTICES_COUNT_LIMIT:
        raise log.AppError(
            text.error.dm_many_verts,
            log.props(
                object=bpy_obj.name,
                vertices_count=vertices_count,
                must_be_no_more_than=fmt.VERTICES_COUNT_LIMIT
            )
        )

    packed_writer.putf('<I', vertices_count)
    packed_writer.putf('<I', len(indices) * 3)

    for vtx in vertices:
        packed_writer.putf(
            '<5f',
            vtx[0][0],
            vtx[0][2],
            vtx[0][1],
            vtx[1][0],
            vtx[1][1]
        )

    for tris in indices:
        packed_writer.putf('<3H', tris[0], tris[2], tris[1])

    bpy.data.meshes.remove(bpy_data)


@log.with_context('export-dm')
def export_file(bpy_obj, file_path, context):
    log.update(object=bpy_obj.name)
    packed_writer = rw.write.PackedWriter()
    export(bpy_obj, packed_writer, context, file_path)
    rw.utils.save_file(file_path, packed_writer)
