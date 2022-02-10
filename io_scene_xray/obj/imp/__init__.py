# addon modules
from . import ops
from . import main
from . import bone
from . import utility
from .. import fmt
from ... import log
from ... import text
from ... import utils
from ... import ie_utils
from ... import xray_io


def _import(file_path, context, reader):
    has_main_chunk = False
    for (cid, data) in reader:
        if cid == fmt.Chunks.Object.MAIN:
            has_main_chunk = True
            chunked_reader = xray_io.ChunkedReader(data)
            bpy_obj = main.import_main(file_path, context, chunked_reader)
            return bpy_obj
        else:
            log.debug('unknown chunk', cid=cid)
    if not has_main_chunk:
        raise utils.AppError(text.error.object_main_chunk)


@log.with_context(name='file')
def import_file(file_path, context):
    log.update(path=file_path)
    ie_utils.check_file_exists(file_path)
    file_data = utils.read_file(file_path)
    chunked_reader = xray_io.ChunkedReader(memoryview(file_data))
    bpy_obj = _import(file_path, context, chunked_reader)
    return bpy_obj
