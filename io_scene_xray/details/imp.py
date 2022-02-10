# standart modules
import os

# blender modules
import bpy

# addon modules
from . import fmt
from . import read
from . import utility
from .. import text
from .. import utils
from .. import log
from .. import xray_io
from .. import version_utils
from .. import ie_utils


def _import(file_path, context, chunked_reader):
    has_header = False
    has_meshes = False
    has_slots = False

    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == 0x0 and not chunk_data:    # bad file (build 1233)
            break

        if chunk_id == fmt.Chunks.HEADER:
            if len(chunk_data) < fmt.HEADER_SIZE:
                raise utils.AppError(text.error.details_bad_header)

            header = read.read_header(xray_io.PackedReader(chunk_data))

            if header.format_version not in fmt.SUPPORT_FORMAT_VERSIONS:
                raise utils.AppError(
                    text.error.details_unsupport_ver,
                    log.props(version=header.format_version)
                )

            has_header = True

        elif chunk_id == fmt.Chunks.MESHES:
            cr_meshes = xray_io.ChunkedReader(chunk_data)
            has_meshes = True

        elif chunk_id == fmt.Chunks.SLOTS:
            if context.load_slots:
                pr_slots = xray_io.PackedReader(chunk_data)
            has_slots = True

    del chunked_reader

    if not has_header:
        raise utils.AppError(text.error.details_no_header)
    if not has_meshes:
        raise utils.AppError(text.error.details_no_meshes)
    if not has_slots and context.load_slots:
        raise utils.AppError(text.error.details_no_slots)

    base_name = os.path.basename(file_path.lower())
    color_indices = utility.generate_color_indices()

    meshes_obj = read.read_details_meshes(
        file_path,
        base_name,
        context,
        cr_meshes,
        color_indices,
        header
    )

    del cr_meshes
    del has_header, has_meshes, has_slots

    if context.load_slots:

        root_obj = bpy.data.objects.new(base_name, None)
        root_obj.xray.is_details = True
        version_utils.link_object(root_obj)

        meshes_obj.parent = root_obj

        slots_base_object, slots_top_object = read.read_details_slots(
            base_name,
            context,
            pr_slots,
            header,
            color_indices,
            root_obj
        )

        del pr_slots

        slots_base_object.parent = root_obj
        slots_top_object.parent = root_obj

        slots = root_obj.xray.detail.slots

        slots.meshes_object = meshes_obj.name
        slots.slots_base_object = slots_base_object.name
        slots.slots_top_object = slots_top_object.name


@log.with_context('import-details')
def import_file(file_path, context):
    log.update(file=file_path)
    ie_utils.check_file_exists(file_path)
    data = utils.read_file(file_path)
    chunked_reader = xray_io.ChunkedReader(data)
    _import(file_path, context, chunked_reader)
