# standart modules
import os

# addon modules
from .. import le
from ... import log
from ... import text
from ... import utils
from ... import rw


def _read_version(data):
    packed_reader = rw.read.PackedReader(data)
    ver = packed_reader.getf('<H')[0]

    # check version
    if ver != le.fmt.GROUP_VERSION:
        raise log.AppError(
            text.error.group_ver,
            log.props(version=ver)
        )


@log.with_context(name='import-group')
@utils.stats.timer
def import_file(file_path, context):
    utils.stats.status('Import File', file_path)
    log.update(file_path=file_path)

    file_data = rw.utils.get_file_data(file_path)

    chunks = rw.utils.get_chunks(file_data)

    # version
    ver_data = chunks.get(le.fmt.GroupChunks.VERSION, None)
    if ver_data:
        _read_version(ver_data)
    else:
        raise log.AppError(text.error.part_no_objs)

    # objects
    chunk_data = chunks.get(le.fmt.GroupChunks.OBJECT_LIST, None)
    if chunk_data:
        refs, pos, rot, scl = le.read.read_objects(chunk_data)
    else:
        raise log.AppError(text.error.part_no_objs)

    # import
    name = os.path.basename(file_path)
    le.imp.import_objects(name, context, refs, pos, rot, scl)
