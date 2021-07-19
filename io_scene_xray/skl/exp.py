import bpy

from ..xray_io import ChunkedWriter, PackedWriter
from ..xray_motions import export_motion, export_motions
from ..utils import save_file, AppError
from .. import context


class ExportSklsContext(context.ExportAnimationOnlyContext):
    def __init__(self):
        context.ExportAnimationOnlyContext.__init__(self)
        self.action = None


def _export_skl(chunked_writer, context):
    writer = PackedWriter()
    export_motion(writer, context.action, context.bpy_arm_obj)
    chunked_writer.put(0x1200, writer)


def export_skl_file(fpath, context):
    writer = ChunkedWriter()
    _export_skl(writer, context)
    save_file(fpath, writer)


def export_skls_file(fpath, context):
    writer = PackedWriter()
    actions = []
    for motion in bpy.context.object.xray.motions_collection:
        action = bpy.data.actions.get(motion.name)
        if action:
            actions.append(action)
    if not actions:
        raise AppError('Active object has no animations')
    export_motions(writer, actions, context.bpy_arm_obj)
    save_file(fpath, writer)
