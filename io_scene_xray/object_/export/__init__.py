
import io

from ... import xray_io
from .. import format_
from . import main
from . import operators


class ExportContext:
    def __init__(
            self,
            textures_folder,
            export_motions,
            soc_sgroups,
            texname_from_path
        ):

        self.textures_folder = textures_folder
        self.export_motions = export_motions
        self.soc_sgroups = soc_sgroups
        self.texname_from_path = texname_from_path


def _export(bpy_obj, chunked_writer, context):
    writer = xray_io.ChunkedWriter()
    main.export_main(bpy_obj, writer, context)
    chunked_writer.put(format_.Chunks.Object.MAIN, writer)


def export_file(bpy_obj, fpath, context):
    with io.open(fpath, 'wb') as file:
        writer = xray_io.ChunkedWriter()
        _export(bpy_obj, writer, context)
        file.write(writer.data)
