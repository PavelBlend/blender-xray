from os.path import splitext, basename

from .xray_io import ChunkedReader, PackedReader
from .xray_motions import import_motion, import_motions
from . import log


class ImportContext:
    def __init__(self, armature, motions_filter):
        self.armature = armature
        self.motions_filter = motions_filter


def _import_skl(fpath, context, chunked_reader):
    name = splitext(basename(fpath.lower()))[0]
    if not context.motions_filter(name):
        return
    for cid, cdata in chunked_reader:
        if cid == 0x1200:
            reader = PackedReader(cdata)
            bonesmap = {b.name.lower(): b for b in context.armature.data.bones}
            act = import_motion(reader, context.armature, bonesmap, set())
            act.name = name
        else:
            log.debug('unknown chunk', cid=cid)


def import_skl_file(fpath, context):
    with open(fpath, 'rb') as file:
        _import_skl(fpath, context, ChunkedReader(file.read()))


def import_skls_file(fpath, context):
    with open(fpath, 'rb') as file:
        reader = PackedReader(file.read())
        import_motions(reader, context.armature, context.motions_filter)
