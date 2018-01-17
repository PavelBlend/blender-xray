
import bpy
import os
import io
from .format import Chunks, SUPPORT_FORMAT_VERSIONS
from ..utils import AppError
from ..xray_io import ChunkedReader, PackedReader
from .utility import generate_color_indices
from . import read


def _import(fpath, cx, cr):

    has_header = False
    has_meshes = False
    has_slots = False

    for chunk_id, chunk_data in cr:

        if chunk_id == 0x0 and len(chunk_data) == 0:    # bad file (build 1233)
            break

        if chunk_id == Chunks.HEADER:

            if len(chunk_data) != 24:
                raise AppError(
                    'bad details file. HEADER chunk size not equal 24'
                    )

            header = read.read_header(PackedReader(chunk_data))

            if header.format_version not in SUPPORT_FORMAT_VERSIONS:
                raise AppError(
                    'unssuported details format version: {}'.format(
                        header.format_version
                        )
                    )

            has_header = True

        elif chunk_id == Chunks.MESHES:
            cr_meshes = ChunkedReader(chunk_data)
            has_meshes = True

        elif chunk_id == Chunks.SLOTS:
            if cx.load_slots:
                pr_slots = PackedReader(chunk_data)
            has_slots = True

    del chunk_data, chunk_id, cr

    if not has_header:
        raise AppError('bad details file. Cannot find HEADER chunk')
    if not has_meshes:
        raise AppError('bad details file. Cannot find MESHES chunk')
    if not has_slots:
        raise AppError('bad details file. Cannot find SLOTS chunk')

    base_name = os.path.basename(fpath.lower())
    color_indices = generate_color_indices()

    meshes_obj = read.read_details_meshes(
        base_name, cx, cr_meshes, color_indices, header
        )

    del cr_meshes
    del has_header, has_meshes, has_slots

    if cx.load_slots:

        root_obj = bpy.data.objects.new(base_name, None)
        bpy.context.scene.objects.link(root_obj)

        meshes_obj.parent = root_obj

        slots_base_object, slots_top_object = read.read_details_slots(
            base_name, cx, pr_slots, header, color_indices, root_obj
            )

        del pr_slots

        slots_base_object.parent = root_obj
        slots_top_object.parent = root_obj

        s = root_obj.xray.detail.slots

        s.meshes_object = meshes_obj.name
        s.slots_base_object = slots_base_object.name
        s.slots_top_object = slots_top_object.name


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, cx, ChunkedReader(f.read()))
