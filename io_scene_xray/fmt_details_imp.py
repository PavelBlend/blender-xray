
import os
import io
from . import fmt_details
from . import fmt_dm_imp
from .utils import AppError
from .xray_io import ChunkedReader, PackedReader


def _read_header(pr):
    fmt_ver, meshes_count, offs_x, offs_z, size_x, size_z = pr.getf('<IIiiII')
    return fmt_ver


def _read_details_meshes(fpath, cx, cr):
    base_name = os.path.basename(fpath.lower())
    root_object = cx.bpy.data.objects.new(base_name, None)
    cx.bpy.context.scene.objects.link(root_object)
    for mesh_id, mesh_data in cr:
        pr = PackedReader(mesh_data)
        mesh_name = '{0} mesh_{1:0>2}'.format(base_name, mesh_id)
        bpy_obj = fmt_dm_imp.import_(mesh_name, cx, pr, mode='DETAILS')
        bpy_obj.parent = root_object


def _import(fpath, cx, cr):
    has_header = False
    has_meshes = False
    for chunk_id, chunk_data in cr:
        if chunk_id == fmt_details.Chunks.HEADER:
            if len(chunk_data) != 24:
                raise AppError(
                    'bad details file. HEADER chunk size not equal 24'
                    )
            format_version = _read_header(PackedReader(chunk_data))
            if format_version not in fmt_details.SUPPORT_FORMAT_VERSIONS:
                raise AppError(
                    'unssuported details format version: {}'.format(
                        format_version
                        )
                    )
            has_header = True
        elif chunk_id == fmt_details.Chunks.MESHES:
            cr_meshes = ChunkedReader(chunk_data)
            has_meshes = True
    if not has_header:
        raise AppError('bad details file. Cannot find HEADER chunk')
    if not has_meshes:
        raise AppError('bad details file. Cannot find MESHES chunk')
    _read_details_meshes(fpath, cx, cr_meshes)


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, cx, ChunkedReader(f.read()))
