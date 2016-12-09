
import os
import io
from . import fmt_details
from . import fmt_dm_imp
from .xray_io import ChunkedReader, PackedReader


def read_header(data):
    if len(data) != 24:
        raise Exception(' ! bad details header data. Header size not equal 24')
    pr = PackedReader(data)
    format_version, meshes_count, \
    offset_x, offset_z, \
    size_x, size_z = pr.getf('<IIiiII')
    return format_version


def _get_details_format_version(data):
    cr = ChunkedReader(data)
    has_header = False
    for chunkId, chunkData in cr:
        if chunkId == fmt_details.Chunks.HEADER:
            has_header = True
            format_version = read_header(chunkData)
            return format_version
    if not has_header:
        raise Exception(' ! bad details file. Cannot find HEADER chunk')


def read_details_meshes(fpath, cx, data):
    base_name = os.path.basename(fpath.lower())
    root_object = cx.bpy.data.objects.new(base_name, None)
    cx.bpy.context.scene.objects.link(root_object)
    cr = ChunkedReader(data)
    for meshId, meshData in cr:
        pr = PackedReader(meshData)
        mesh_name = base_name + ' mesh_' + str(meshId)
        bpy_obj = fmt_dm_imp._import(mesh_name, cx, pr, mode='DETAILS')
        bpy_obj.parent = root_object


def _import(fpath, cx, cr):
    for chunkId, chunkData in cr:
        if chunkId == fmt_details.Chunks.MESHES:
            read_details_meshes(fpath, cx, chunkData)


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        file_data = f.read()
        format_version = _get_details_format_version(file_data)
        if format_version in fmt_details.SUPPORT_FORMAT_VERSIONS:
            _import(fpath, cx, ChunkedReader(file_data))
        else:
            raise Exception(' ! unssuported details format version: {}'.format(format_version))
