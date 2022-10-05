# blender modules
import bpy

# addon modules
from .. import contexts
from .. import motions
from ... import rw
from ... import log
from ... import utils


class ExportSklsContext(contexts.ExportAnimationOnlyContext):
    def __init__(self):
        super().__init__()
        self.action = None


def _export_skl(chunked_writer, context):
    arm_obj = context.bpy_arm_obj
    (
        current_frame,
        mode,
        current_action,
        dependency_object,
        dep_action
    ) = utils.action.get_initial_state(arm_obj)

    writer = rw.write.PackedWriter()
    motions.exp.export_motion(writer, context.action, arm_obj)
    chunked_writer.put(0x1200, writer)

    utils.action.set_initial_state(
        arm_obj,
        mode,
        current_frame,
        current_action,
        dependency_object,
        dep_action
    )


@log.with_context(name='export-skl')
def export_skl_file(file_path, context):
    log.update(action=context.action.name)
    writer = rw.write.ChunkedWriter()
    _export_skl(writer, context)
    rw.utils.save_file(file_path, writer)


@log.with_context(name='export-skls')
def export_skls_file(file_path, context, actions):
    log.update(object=context.bpy_arm_obj.name)
    writer = rw.write.PackedWriter()
    motions.exp.export_motions(writer, actions, context.bpy_arm_obj)
    rw.utils.save_file(file_path, writer)
