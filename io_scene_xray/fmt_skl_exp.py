import bpy

from .xray_io import ChunkedWriter, PackedWriter
from .xray_motions import export_motion, export_motions


class ExportContext:
    def __init__(self, armature, action=None):
        self.armature = armature
        self.action = action


def _export_skl(chunked_writer, context):
    writer = PackedWriter()
    export_motion(writer, context.action, context.armature)
    chunked_writer.put(0x1200, writer)


def export_skl_file(fpath, context):
    with open(fpath, 'wb') as file:
        writer = ChunkedWriter()
        _export_skl(writer, context)
        file.write(writer.data)


def export_skls_file(fpath, context):
    with open(fpath, 'wb') as file:
        writer = PackedWriter()
        export_motions(writer, bpy.data.actions, context.armature)
        file.write(writer.data)
