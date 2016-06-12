import bpy
import io
from .xray_io import ChunkedWriter, PackedWriter
from .xray_motions import export_motion, export_motions


class ExportContext:
    def __init__(self, report, armature, action=None):
        self.report = report
        self.armature = armature
        self.action = action


def _export_skl(cw, cx):
    pw = PackedWriter()
    export_motion(pw, cx.action, cx, cx.armature)
    cw.put(0x1200, pw)


def export_skl_file(fpath, cx):
    with io.open(fpath, 'wb') as f:
        cw = ChunkedWriter()
        _export_skl(cw, cx)
        f.write(cw.data)


def export_skls_file(fpath, cx):
    with io.open(fpath, 'wb') as f:
        pw = PackedWriter()
        export_motions(pw, bpy.data.actions, cx, cx.armature)
        f.write(pw.data)
