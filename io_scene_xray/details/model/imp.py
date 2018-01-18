
import io
import os
from ...xray_io import PackedReader
from .create import create_object, search_material, create_mesh
from .fmt import DetailModel


def import_(fpath, cx, pr, mode='DM', detail_index=None, detail_colors=None):

    dm = DetailModel()

    object_name = os.path.basename(fpath.lower())
    bpy_obj, bpy_mesh = create_object(cx, object_name)

    dm.shader = pr.gets()
    dm.texture = pr.gets()
    dm.mode = mode
    dm.mesh.bpy_mesh = bpy_mesh

    cx.os = os
    bpy_material = search_material(cx, dm)

    dm.mesh.bpy_mesh.materials.append(bpy_material)
    dm.mesh.bpy_material = bpy_material

    flags, min_scale, max_scale, verts_cnt, indices_cnt = pr.getf('<IffII')

    dm.mesh.vertices_count = verts_cnt
    dm.mesh.indices_count = indices_cnt

    model = bpy_obj.xray.detail.model

    model.no_waving = bool(flags)
    model.min_scale = min_scale
    model.max_scale = max_scale

    if dm.mode == 'DETAILS':
        model.index = detail_index
        model.color = detail_colors[detail_index][0:3]

    create_mesh(cx, pr, dm, PackedReader)

    return bpy_obj


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        import_(fpath, cx, PackedReader(f.read()))
