# blender modules
import bpy

# addon modules
from .. import contexts
from ... import rw
from ... import motions
from ... import log
from ... import utils


class ExportSklsContext(contexts.ExportAnimationOnlyContext):
    def __init__(self):
        super().__init__()
        self.action = None


def _export_skl(chunked_writer, context):
    writer = rw.write.PackedWriter()
    motions.exp.export_motion(writer, context.action, context.bpy_arm_obj)
    chunked_writer.put(0x1200, writer)


@log.with_context(name='export-skl')
def export_skl_file(file_path, context):
    log.update(action=context.action.name)
    writer = rw.write.ChunkedWriter()
    _export_skl(writer, context)
    utils.save_file(file_path, writer)


@log.with_context(name='export-skls')
def export_skls_file(file_path, context, actions):
    log.update(object=context.bpy_arm_obj.name)
    writer = rw.write.PackedWriter()
    motions.exp.export_motions(writer, actions, context.bpy_arm_obj)
    utils.save_file(file_path, writer)
