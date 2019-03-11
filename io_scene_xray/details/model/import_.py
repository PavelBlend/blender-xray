
import io
import os

from ... import xray_io
from . import create
from . import format_


def import_(fpath, context, packed_reader, mode='DM', detail_index=None,
        detail_colors=None):

    det_model = format_.DetailModel()

    object_name = os.path.basename(fpath.lower())
    bpy_obj, bpy_mesh = create.create_object(object_name)

    det_model.shader = packed_reader.gets()
    det_model.texture = packed_reader.gets()
    det_model.mode = mode
    det_model.mesh.bpy_mesh = bpy_mesh

    context.os = os
    bpy_material = create.search_material(context, det_model, fpath=fpath)

    det_model.mesh.bpy_mesh.materials.append(bpy_material)
    det_model.mesh.bpy_material = bpy_material

    flags, min_scale, max_scale, verts_cnt, indices_cnt = \
        packed_reader.getf('<IffII')

    det_model.mesh.vertices_count = verts_cnt
    det_model.mesh.indices_count = indices_cnt

    model = bpy_obj.xray.detail.model

    model.no_waving = bool(flags)
    model.min_scale = min_scale
    model.max_scale = max_scale

    if det_model.mode == 'DETAILS':
        model.index = detail_index
        model.color = detail_colors[detail_index][0:3]

    create.create_mesh(packed_reader, det_model)

    return bpy_obj


def import_file(fpath, context):
    with io.open(fpath, 'rb') as file:
        import_(fpath, context, xray_io.PackedReader(file.read()))
