# standart modules
import os

# blender modules
import bpy

# addon modules
from . import fmt
from . import read
from . import utility
from ... import text
from ... import utils
from ... import log
from ... import rw


def _import(file_path, context, chunked_reader):
    context.level_name = os.path.basename(os.path.dirname(file_path))

    has_header = False
    has_meshes = False
    has_slots = False

    for chunk_id, chunk_data in chunked_reader:

        # bad file (build 1233)
        if chunk_id == 0x0 and not chunk_data:
            break

        # header
        if chunk_id == fmt.Chunks.HEADER:
            if len(chunk_data) < fmt.HEADER_SIZE:
                raise log.AppError(text.error.details_bad_header)

            header = read.read_header(rw.read.PackedReader(chunk_data))
            has_header = True

        # meshes
        elif chunk_id == fmt.Chunks.MESHES:
            cr_meshes = rw.read.ChunkedReader(chunk_data)
            has_meshes = True

        # slots
        elif chunk_id == fmt.Chunks.SLOTS:
            if context.load_slots:
                pr_slots = rw.read.PackedReader(chunk_data)
            has_slots = True

    if not has_header:
        raise log.AppError(text.error.details_no_header)

    if not has_meshes:
        raise log.AppError(text.error.details_no_meshes)

    if not has_slots and context.load_slots:
        raise log.AppError(text.error.details_no_slots)

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

    if context.load_slots:

        root_obj = bpy.data.objects.new(base_name, None)
        root_obj.xray.is_details = True
        utils.version.link_object(root_obj)
        utils.stats.created_obj()

        meshes_obj.parent = root_obj

        slots_base_object, slots_top_object = read.read_details_slots(
            base_name,
            context,
            pr_slots,
            header,
            color_indices,
            root_obj
        )

        slots_base_object.parent = root_obj
        slots_top_object.parent = root_obj

        slots = root_obj.xray.detail.slots

        slots.meshes_object = meshes_obj.name
        slots.slots_base_object = slots_base_object.name
        slots.slots_top_object = slots_top_object.name


@log.with_context('import-details')
@utils.stats.timer
def import_file(file_path, context):
    utils.stats.status('Import File', file_path)

    chunked_reader = rw.utils.get_file_reader(file_path, chunked=True)
    _import(file_path, context, chunked_reader)
