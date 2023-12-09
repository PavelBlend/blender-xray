# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import le
from ... import log
from ... import text
from ... import utils
from ... import rw


@log.with_context(name='import-group')
@utils.stats.timer
def import_file(file_path, context):
    utils.stats.status('Import File', file_path)

    file_data = rw.utils.get_file_data(file_path)

    chunks = rw.utils.get_chunks(file_data)
    chunk_data = chunks.get(le.fmt.GroupChunks.OBJECT_LIST, None)

    if chunk_data:
        refs, pos, rot, scl = le.read.read_objects(chunk_data)
    else:
        raise log.AppError(text.error.part_no_objs)

    # import
    name = os.path.basename(file_path)
    objs, coll = le.imp.import_objects(name, context, refs, pos, rot, scl)
