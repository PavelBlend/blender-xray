import bpy

from ..xray_io import ChunkedWriter, PackedWriter
from ..xray_motions import export_motion, export_motions


class ExportContext:
    def __init__(self, armature, action=None):
        self.armature = armature
        self.action = action


def _export_skl(chunked_writer, context):
    writer = PackedWriter()
    export_motion(writer, context.action, context.armature)
    chunked_writer.put(0x1200, writer)


def export_skl_file(fpath, context):
    writer = ChunkedWriter()
    _export_skl(writer, context)
    file = open(fpath, 'wb')
    file.write(writer.data)
    file.close()


def export_skls_file(fpath, context):
    writer = PackedWriter()
    actions = []
    for motion in bpy.context.object.xray.motions_collection:
        action = bpy.data.actions[motion.name]
        actions.append(action)
    export_motions(writer, actions, context.armature)
    file = open(fpath, 'wb')
    file.write(writer.data)
    file.close()
