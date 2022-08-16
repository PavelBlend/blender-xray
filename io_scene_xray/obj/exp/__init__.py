# addon modules
from . import ops
from . import main
from .. import fmt
from ... import rw
from ... import utils


def _export(bpy_obj, chunked_writer, context):
    writer = rw.xray_io.ChunkedWriter()
    main.export_main(bpy_obj, writer, context)
    chunked_writer.put(fmt.Chunks.Object.MAIN, writer)


def export_file(bpy_obj, file_path, context):
    writer = rw.xray_io.ChunkedWriter()
    _export(bpy_obj, writer, context)
    utils.save_file(file_path, writer)
