
import io

import bpy
import bmesh
import mathutils

from ... import utils
from ... import xray_io
from . import validate
from . import format_


def export(bpy_obj, packed_writer, context, mode='DM'):

    bpy_material, tx_name = validate.validate_export_object(context, bpy_obj)

    det_model = bpy_obj.xray.detail.model
    packed_writer.puts(bpy_material.xray.eshader)
    packed_writer.puts(tx_name)
    packed_writer.putf('<I', int(det_model.no_waving))
    packed_writer.putf('<ff', det_model.min_scale, det_model.max_scale)

    if mode == 'DM':
        b_mesh = utils.convert_object_to_space_bmesh(
            bpy_obj, mathutils.Matrix.Identity(4)
            )

    else:
        b_mesh = utils.convert_object_to_space_bmesh(
            bpy_obj, mathutils.Matrix.Identity(4), local=True
            )

    bmesh.ops.triangulate(b_mesh, faces=b_mesh.faces)
    bpy_data = bpy.data.meshes.new('.export-dm')
    b_mesh.to_mesh(bpy_data)
    bml_uv = b_mesh.loops.layers.uv.active
    vertices = []
    indices = []
    vmap = {}

    if mode == 'DM':
        for face in b_mesh.faces:
            _ = []
            for loop in face.loops:
                uv = loop[bml_uv].uv
                vtx = (loop.vert.co.to_tuple(), (uv[0], uv[1]))
                vi = vmap.get(vtx)
                if vi is None:
                    vmap[vtx] = vi = len(vertices)
                    vertices.append(vtx)
                _.append(vi)
            indices.append(_)

    else:
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
    if vertices_count > format_.VERTICES_COUNT_LIMIT:
        raise utils.AppError(
            'mesh "' + bpy_obj.data.name + \
            '" has too many vertices: {}. Must be no more than {}'.format(
                vertices_count, format_.VERTICES_COUNT_LIMIT
                )
            )

    packed_writer.putf('<I', vertices_count)
    packed_writer.putf('<I', len(indices) * 3)

    for vtx in vertices:
        packed_writer.putf(
            '<5f', vtx[0][0], vtx[0][2], vtx[0][1], vtx[1][0], vtx[1][1]
            )

    for tris in indices:
        packed_writer.putf('<3H', tris[0], tris[2], tris[1])

    bpy.data.meshes.remove(bpy_data)


def export_file(bpy_obj, fpath, context):
    with io.open(fpath, 'wb') as file:
        packed_writer = xray_io.PackedWriter()
        export(bpy_obj, packed_writer, context)
        file.write(packed_writer.data)
