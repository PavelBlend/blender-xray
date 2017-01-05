
import io
import bpy
import bmesh
import mathutils

from io_scene_xray.utils import (
    convert_object_to_space_bmesh, AppError, gen_texture_name
    )

from io_scene_xray.xray_io import PackedWriter
from .validate import validate_export_object
from .format import VERTICES_COUNT_LIMIT


def export(bpy_obj, pw, cx, mode='DM'):

    bpy_material, tx_name = validate_export_object(cx, bpy_obj)

    m = bpy_obj.xray.detail.model
    pw.puts(bpy_material.xray.eshader)
    pw.puts(tx_name)
    pw.putf('<I', int(m.no_waving))
    pw.putf('<ff', m.min_scale, m.max_scale)

    if mode == 'DM':
        bm = convert_object_to_space_bmesh(
            bpy_obj, mathutils.Matrix.Identity(4)
            )

    else:
        bm = convert_object_to_space_bmesh(
            bpy_obj, mathutils.Matrix.Identity(4), local=True
            )

    bmesh.ops.triangulate(bm, faces=bm.faces)
    bpy_data = bpy.data.meshes.new('.export-dm')
    bm.to_mesh(bpy_data)
    bml_uv = bm.loops.layers.uv.active
    vertices = []
    indices = []
    vmap = {}

    if mode == 'DM':
        for f in bm.faces:
            ii = []
            for li, l in enumerate(f.loops):
                dl = bpy_data.loops[f.index * 3 + li]
                uv = l[bml_uv].uv
                vtx = (l.vert.co.to_tuple(), (uv[0], uv[1]))
                vi = vmap.get(vtx)
                if vi is None:
                    vmap[vtx] = vi = len(vertices)
                    vertices.append(vtx)
                ii.append(vi)
            indices.append(ii)

    else:
        for f in bm.faces:
            ii = []
            for li, l in enumerate(f.loops):
                dl = bpy_data.loops[f.index * 3 + li]
                uv = l[bml_uv].uv
                vtx = (l.vert.co.to_tuple(), (uv[0], 1 - uv[1]))
                vi = vmap.get(vtx)
                if vi is None:
                    vmap[vtx] = vi = len(vertices)
                    vertices.append(vtx)
                ii.append(vi)
            indices.append(ii)

    vertices_count = len(vertices)
    if vertices_count > VERTICES_COUNT_LIMIT:
        raise AppError(
            'mesh "' + bpy_obj.data.name + \
            '" has too many vertices. Must be no more than {}'.format(
                VERTICES_COUNT_LIMIT
                )
            )

    pw.putf('<I', vertices_count)
    pw.putf('<I', len(indices) * 3)

    for vtx in vertices:
        pw.putf(
            '<fffff', vtx[0][0], vtx[0][2], vtx[0][1], vtx[1][0], vtx[1][1]
            )

    for tris in indices:
        pw.putf('<HHH', tris[0], tris[2], tris[1])

    bpy.data.meshes.remove(bpy_data)


def export_file(bpy_obj, fpath, cx):
    with io.open(fpath, 'wb') as f:
        pw = PackedWriter()
        export(bpy_obj, pw, cx)
        f.write(pw.data)
