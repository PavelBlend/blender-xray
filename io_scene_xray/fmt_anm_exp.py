import io
import bpy
from .xray_io import ChunkedWriter, PackedWriter
from .fmt_anm import Chunks
from .xray_envelope import export_envelope, EPSILON
from .utils import smooth_euler


class ExportContext:
    def __init__(self, report):
        self.report = report


def _export(bpy_obj, cw, cx):
    assert bpy_obj.animation_data, 'Animation: object doesn\'t any animation data'
    pw = PackedWriter()
    bpy_act = bpy_obj.animation_data.action
    pw.puts('')
    fr = bpy_act.frame_range
    pw.putf('II', int(fr[0]), int(fr[1]))
    fps = bpy_act.xray.fps
    pw.putf('fH', fps, 5)
    if bpy_act.xray.autobake:
        baked_action = bpy.data.actions.new('')
        try:
            _bake_to_action(bpy_obj, baked_action, fr)
            _export_action_data(pw, bpy_act.xray, baked_action.fcurves, cx)
        finally:
            bpy.data.actions.remove(baked_action, do_unlink=True)
    else:
        assert bpy_obj.rotation_mode == 'YXZ', 'Animation: rotation mode must be \'YXZ\''
        _export_action_data(pw, bpy_act.xray, bpy_act.fcurves, cx)
    cw.put(Chunks.MAIN, pw)


def _bake_to_action(bobject, action, frange):
    old_frame = bpy.context.scene.frame_current
    try:
        group_name = 'LocRot'
        fc_trn = [
            action.fcurves.new('location', 0, group_name),
            action.fcurves.new('location', 1, group_name),
            action.fcurves.new('location', 2, group_name),
        ]
        fc_rot = [
            action.fcurves.new('rotation_euler', 0, group_name),
            action.fcurves.new('rotation_euler', 1, group_name),
            action.fcurves.new('rotation_euler', 2, group_name)
        ]
        prev_rot = None
        for frm in range(int(frange[0]), int(frange[1]) + 1):
            bpy.context.scene.frame_set(frm)
            bpy.context.scene.update()
            mat = bobject.matrix_world
            trn = mat.to_translation()
            rot = mat.to_euler('YXZ')
            if prev_rot:
                smooth_euler(rot, prev_rot)
            prev_rot = rot
            for i in range(3):
                fc_trn[i].keyframe_points.insert(frm, trn[i]).interpolation = 'LINEAR'
                fc_rot[i].keyframe_points.insert(frm, rot[i]).interpolation = 'LINEAR'
    finally:
        bpy.context.scene.frame_set(old_frame)


def _export_action_data(pkw, xray, fcurves, ctx):
    for i in range(6):
        fcurve = fcurves[(0, 2, 1, 5, 3, 4)[i]]
        kv = (1, 1, 1, -1, -1, -1)[i]
        epsilon = EPSILON
        if xray.autobake_custom_refine:
            epsilon = xray.autobake_refine_location if i < 3 else xray.autobake_refine_location
        export_envelope(
            pkw, fcurve,
            xray.fps, kv,
            warn=lambda msg: ctx.report({'WARNING'}, msg),
            epsilon=epsilon
        )


def export_file(bpy_obj, fpath, cx):
    with io.open(fpath, 'wb') as f:
        cw = ChunkedWriter()
        _export(bpy_obj, cw, cx)
        f.write(cw.data)
