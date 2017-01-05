
import io
from io_scene_xray.xray_io import ChunkedWriter
from .write import write_header, write_details, write_slots

from .convert import (
    convert_bpy_data_to_level_details_struct,
    convert_bpy_data_to_slots_transforms
    )


def _export(bpy_obj, cw, cx):

    ld = convert_bpy_data_to_level_details_struct(cx, bpy_obj)
    convert_bpy_data_to_slots_transforms(ld)

    write_details(cw, ld, cx)
    write_slots(cw, ld)
    write_header(cw, ld)


def export_file(bpy_obj, fpath, cx):
    with io.open(fpath, 'wb') as f:
        cw = ChunkedWriter()
        _export(bpy_obj, cw, cx)
        f.write(cw.data)
