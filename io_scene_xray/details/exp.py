from .. import xray_io
from .. import utils
from . import write, convert


def _export(bpy_obj, chunked_writer, context, fpath):

    lvl_dets = convert.bpy_data_to_lvl_dets_struct(context, bpy_obj)
    convert.bpy_data_to_slots_transforms(lvl_dets)
    convert.validate_images_size(lvl_dets)

    if context.level_details_format_version == 'builds_1569-cop':
        write.write_details(chunked_writer, lvl_dets, context, fpath)
        write.write_slots_v3(chunked_writer, lvl_dets)
        write.write_header(chunked_writer, lvl_dets)

    elif context.level_details_format_version in {
            'builds_1096-1230', 'builds_1233-1558'
        }:
        write.write_header(chunked_writer, lvl_dets)
        write.write_details(chunked_writer, lvl_dets, context, fpath)
        write.write_slots_v2(chunked_writer, lvl_dets)


def export_file(bpy_obj, fpath, context):
    chunked_writer = xray_io.ChunkedWriter()
    _export(bpy_obj, chunked_writer, context, fpath)
    utils.save_file(fpath, chunked_writer)
