# standart modules
import os

# addon modules
from .. import log
from .. import contexts
from .. import xray_io
from .. import xray_motions


class ImportSklContext(contexts.ImportAnimationOnlyContext):
    def __init__(self):
        contexts.ImportAnimationOnlyContext.__init__(self)
        self.filename = None


def _import_skl(fpath, context, chunked_reader):
    basename = os.path.basename(fpath.lower())
    name = os.path.splitext(basename)[0]
    if not context.motions_filter(name):
        return
    for cid, cdata in chunked_reader:
        if cid == 0x1200:
            reader = xray_io.PackedReader(cdata)
            bonesmap = {
                b.name.lower(): b for b in context.bpy_arm_obj.data.bones
            }
            act = xray_motions.import_motion(
                reader, context, bonesmap, set(), skl_file_name=name
            )
            act.name = name
        else:
            log.debug('unknown chunk', cid=cid)


def import_skl_file(fpath, context):
    with open(fpath, 'rb') as file:
        _import_skl(fpath, context, xray_io.ChunkedReader(file.read()))


def import_skls_file(fpath, context):
    with open(fpath, 'rb') as file:
        reader = xray_io.PackedReader(file.read())
        xray_motions.import_motions(reader, context, context.motions_filter)
