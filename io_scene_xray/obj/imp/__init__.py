# addon modules
from . import ops
from . import main
from . import bone
from . import utility
from .. import fmt
from ... import log
from ... import xray_io


def _import(fpath, context, reader):
    for (cid, data) in reader:
        if cid == fmt.Chunks.Object.MAIN:
            bpy_obj = main.import_main(fpath, context, xray_io.ChunkedReader(data))
            return bpy_obj
        else:
            log.debug('unknown chunk', cid=cid)


@log.with_context(name='file')
def import_file(fpath, context):
    log.update(path=fpath)
    with open(fpath, 'rb') as file:
        bpy_obj = _import(fpath, context, xray_io.ChunkedReader(memoryview(file.read())))
        return bpy_obj
