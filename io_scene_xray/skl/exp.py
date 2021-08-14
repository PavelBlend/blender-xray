# blender modules
import bpy

# addon modules
from .. import contexts
from .. import xray_io
from .. import xray_motions
from .. import utils


class ExportSklsContext(contexts.ExportAnimationOnlyContext):
    def __init__(self):
        contexts.ExportAnimationOnlyContext.__init__(self)
        self.action = None


def _export_skl(chunked_writer, context):
    writer = xray_io.PackedWriter()
    xray_motions.export_motion(writer, context.action, context.bpy_arm_obj)
    chunked_writer.put(0x1200, writer)


def export_skl_file(fpath, context):
    writer = xray_io.ChunkedWriter()
    _export_skl(writer, context)
    utils.save_file(fpath, writer)


def export_skls_file(fpath, context):
    writer = xray_io.PackedWriter()
    actions = []
    for motion in bpy.context.object.xray.motions_collection:
        action = bpy.data.actions.get(motion.name)
        if action:
            actions.append(action)
    if not actions:
        raise utils.AppError('Active object has no animations')
    xray_motions.export_motions(writer, actions, context.bpy_arm_obj)
    utils.save_file(fpath, writer)
