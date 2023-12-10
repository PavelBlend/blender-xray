# addon modules
from .. import le
from ... import rw
from ... import log
from ... import utils


def write_header(chunked_writer):
    packed_writer = rw.write.PackedWriter()

    packed_writer.putf('<I', le.fmt.SCENE_VERSION)

    chunked_writer.put(le.fmt.SceneChunks.VERSION, packed_writer)


def _export(bpy_objs, chunked_writer):
    write_header(chunked_writer)
    le.write.write_objects(chunked_writer, bpy_objs)


@log.with_context(name='export-scene-selection')
@utils.stats.timer
def export_file(bpy_objs, file_path):
    utils.stats.status('Export File', file_path)
    log.update(file_path=file_path)

    writer = rw.write.ChunkedWriter()
    _export(bpy_objs, writer)
    rw.utils.save_file(file_path, writer)
