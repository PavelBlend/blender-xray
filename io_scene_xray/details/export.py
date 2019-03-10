
import io
from ..xray_io import ChunkedWriter
from .write import write_header, write_details, write_slots_v3, write_slots_v2

from .convert import (
    bpy_data_to_lvl_dets_struct,
    bpy_data_to_slots_transforms,
    validate_images_size
    )


def _export(bpy_obj, chunked_writer, context):

    lvl_dets = bpy_data_to_lvl_dets_struct(context, bpy_obj)
    bpy_data_to_slots_transforms(lvl_dets)
    validate_images_size(lvl_dets)

    if context.level_details_format_version == 'builds_1569-cop':
        write_details(chunked_writer, lvl_dets, context)
        write_slots_v3(chunked_writer, lvl_dets)
        write_header(chunked_writer, lvl_dets)

    elif context.level_details_format_version in {
            'builds_1096-1230', 'builds_1233-1558'
        }:
        write_header(chunked_writer, lvl_dets)
        write_details(chunked_writer, lvl_dets, context)
        write_slots_v2(chunked_writer, lvl_dets)


def export_file(bpy_obj, fpath, context):
    with io.open(fpath, 'wb') as file:
        chunked_writer = ChunkedWriter()
        _export(bpy_obj, chunked_writer, context)
        file.write(chunked_writer.data)
