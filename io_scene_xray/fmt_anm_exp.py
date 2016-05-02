import io
from .xray_io import ChunkedWriter, PackedWriter
from .fmt_anm import Chunks
from .xray_envelope import export_envelope


class ExportContext:
    def __init__(self, report):
        self.report = report


def _export(bpy_obj, cw, cx):
    assert bpy_obj.rotation_mode == 'YXZ', 'Animation: rotation mode must be \'YXZ\''
    pw = PackedWriter()
    bpy_act = bpy_obj.animation_data.action
    pw.puts('')
    fr = bpy_act.frame_range
    pw.putf('II', int(fr[0]), int(fr[1]))
    fps = 30
    pw.putf('fH', fps, 5)

    for i in range(6):
        fc = bpy_act.fcurves[(0, 2, 1, 5, 3, 4)[i]]
        kv = (1, 1, 1, -1, -1, -1)[i]
        export_envelope(pw, fc, fps, kv, warn=lambda msg: cx.report({'WARNING'}, msg))
    cw.put(Chunks.MAIN, pw)


def export_file(bpy_obj, fpath, cx):
    with io.open(fpath, 'wb') as f:
        cw = ChunkedWriter()
        _export(bpy_obj, cw, cx)
        f.write(cw.data)
