
import io
from io_scene_xray.xray_io import ChunkedWriter
from .write import write_header, write_details, write_slots_v3, write_slots_v2

from .convert import (
    convert_bpy_data_to_level_details_struct,
    convert_bpy_data_to_slots_transforms,
    validate_images_size
    )


def _export(bpy_obj, cw, cx):

    ld = convert_bpy_data_to_level_details_struct(cx, bpy_obj)
    convert_bpy_data_to_slots_transforms(ld)
    validate_images_size(ld)

    if cx.level_details_format_version == 'NEW':
        write_details(cw, ld, cx)
        write_slots_v3(cw, ld)
        write_header(cw, ld)

    elif cx.level_details_format_version in {'OLD_1', 'OLD_2'}:
        write_header(cw, ld)
        write_details(cw, ld, cx)
        write_slots_v2(cw, ld)


def export_file(bpy_obj, fpath, cx):
    with io.open(fpath, 'wb') as f:
        cw = ChunkedWriter()
        _export(bpy_obj, cw, cx)
        f.write(cw.data)
