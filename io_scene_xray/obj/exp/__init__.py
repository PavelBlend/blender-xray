from ... import xray_io, utils
from .. import fmt
from . import main


def _export(bpy_obj, chunked_writer, context):
    writer = xray_io.ChunkedWriter()
    main.export_main(bpy_obj, writer, context)
    chunked_writer.put(fmt.Chunks.Object.MAIN, writer)


def export_file(bpy_obj, fpath, context):
    writer = xray_io.ChunkedWriter()
    _export(bpy_obj, writer, context)
    utils.save_file(fpath, writer)
