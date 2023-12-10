# standart modules
import os

# addon modules
from .. import le
from ... import rw
from ... import log
from ... import text
from ... import utils


def write_guid(file_path, chunked_writer):
    packed_writer = rw.write.PackedWriter()

    if os.path.exists(file_path):

        with open(file_path, 'rb') as file:
            data = file.read()

        chunked_reader = rw.read.ChunkedReader(data)
        guid_data = chunked_reader.get_chunk(le.fmt.ToolsChunks.GUID)

        if guid_data is None:
            raise log.AppError(
                text.error.part_no_guid,
                log.props(file=file_path)
            )

        packed_writer.data = guid_data

    else:
        raise log.AppError(text.error.part_no_file)

    chunked_writer.put(le.fmt.ToolsChunks.GUID, packed_writer)


def _export(file_path, objs, chunked_writer):
    write_guid(file_path, chunked_writer)
    le.write.write_objects(chunked_writer, objs, part=True)


@log.with_context(name='export-part')
@utils.stats.timer
def export_file(objs, file_path):
    utils.stats.status('Export File', file_path)
    log.update(file_path=file_path)

    writer = rw.write.ChunkedWriter()
    _export(file_path, objs, writer)
    rw.utils.save_file(file_path, writer)
