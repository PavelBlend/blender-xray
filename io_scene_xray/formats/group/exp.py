# standart modules
import os

# blender modules
import mathutils

# addon modules
from .. import le
from ... import rw
from ... import log
from ... import utils


def _write_group_version(chunked_writer):
    packed_reader = rw.write.PackedWriter()

    packed_reader.putf('<H', le.fmt.GROUP_VERSION)

    chunked_writer.put(le.fmt.GroupChunks.VERSION, packed_reader)


def _write_flags(chunked_writer):
    packed_reader = rw.write.PackedWriter()

    packed_reader.putf('<I', 0)

    chunked_writer.put(le.fmt.GroupChunks.FLAGS, packed_reader)


def _write_reference(chunked_writer):
    packed_reader = rw.write.PackedWriter()

    packed_reader.puts('')

    chunked_writer.put(le.fmt.GroupChunks.REFERENCE, packed_reader)


def _export(file_path, objs, chunked_writer):
    object_name = os.path.splitext(os.path.basename(file_path))[0]

    le.write.write_flags(chunked_writer)
    le.write.write_name(object_name, chunked_writer)

    le.write.write_transform(
        mathutils.Vector((0.0, 0.0, 0.0)),    # position
        mathutils.Euler((0.0, 0.0, 0.0)),    # rotation
        mathutils.Vector((1.0, 1.0, 1.0)),    # scale
        chunked_writer
    )

    _write_group_version(chunked_writer)
    _write_flags(chunked_writer)
    le.write.write_scene_objects(chunked_writer, objs, group=True)
    _write_reference(chunked_writer)


@log.with_context(name='export-group')
@utils.stats.timer
def export_file(objs, file_path):
    utils.stats.status('Export File', file_path)

    writer = rw.write.ChunkedWriter()
    _export(file_path, objs, writer)
    rw.utils.save_file(file_path, writer)
