# standart modules
import os

# addon modules
from . import fmt
from . import create
from ... import log
from ... import rw
from ... import utils


def import_(
        file_path,
        context,
        packed_reader,
        mode='DM',
        detail_index=None,
        detail_colors=None
    ):
    det_model = fmt.DetailModel()

    object_name = os.path.basename(file_path.lower())
    bpy_obj, bpy_mesh = create.create_object(object_name)

    det_model.shader = packed_reader.gets()
    det_model.texture = packed_reader.gets()
    det_model.mode = mode
    det_model.mesh.bpy_mesh = bpy_mesh

    context.os = os
    bpy_material = create.search_material(
        context,
        det_model,
        file_path=file_path
    )

    det_model.mesh.bpy_mesh.materials.append(bpy_material)
    det_model.mesh.bpy_material = bpy_material

    flags, min_scale, max_scale, verts_cnt, indices_cnt = packed_reader.getf(
        '<I2f2I'
    )

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


@log.with_context('import-dm')
@utils.stats.timer
def import_file(file_path, context):
    utils.stats.status('Import File', file_path)

    packed_reader = rw.utils.get_file_reader(file_path, chunked=False)
    import_(file_path, context, packed_reader)
