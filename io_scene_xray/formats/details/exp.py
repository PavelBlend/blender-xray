# addon modules
from . import convert
from . import write
from ... import log
from ... import rw
from ... import utils


def _export(bpy_obj, chunked_writer, context, file_path):

    lvl_dets = convert.bpy_data_to_lvl_dets_struct(context, bpy_obj)
    convert.bpy_data_to_slots_transforms(lvl_dets)
    convert.validate_images_size(lvl_dets)

    if context.level_details_format_version == 'builds_1569-cop':
        write.write_details(chunked_writer, lvl_dets, context, file_path)
        write.write_slots_v3(chunked_writer, lvl_dets)
        write.write_header(chunked_writer, lvl_dets)

    else:
        write.write_header(chunked_writer, lvl_dets)
        write.write_details(chunked_writer, lvl_dets, context, file_path)
        write.write_slots_v2(chunked_writer, lvl_dets)


@log.with_context('export-details')
@utils.stats.timer
def export_file(bpy_obj, file_path, context):
    utils.stats.status('Export File: "{}"'.format(file_path))

    log.update(object=bpy_obj.name)
    chunked_writer = rw.write.ChunkedWriter()
    _export(bpy_obj, chunked_writer, context, file_path)
    rw.utils.save_file(file_path, chunked_writer)
