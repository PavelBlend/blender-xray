from io import open
from os.path import splitext, basename
from .xray_io import ChunkedReader, PackedReader
from .xray_motions import import_motion, import_motions
from . import log


class ImportContext:
    def __init__(self, armature):
        self.armature = armature


def _import_skl(fpath, cx, cr):
    for cid, cdata in cr:
        if cid == 0x1200:
            pr = PackedReader(cdata)
            bonesmap = {b.name.lower(): b for b in cx.armature.data.bones}
            act = import_motion(pr, cx.armature, bonesmap, set())
            act.name = splitext(basename(fpath.lower()))[0]
        else:
            log.warn('unknown chunk', cid=cid)


def import_skl_file(fpath, cx):
    with open(fpath, 'rb') as f:
        _import_skl(fpath, cx, ChunkedReader(f.read()))


def import_skls_file(fpath, cx):
    with open(fpath, 'rb') as f:
        pr = PackedReader(f.read())
        import_motions(pr, cx.armature)
