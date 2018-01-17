import io
import bpy
from .xray_io import ChunkedWriter, PackedWriter
from .fmt_anm import Chunks
from .xray_envelope import export_envelope, EPSILON
from .utils import smooth_euler


def _export(bpy_obj, chunked_writer):
    assert bpy_obj.animation_data, 'Animation: object doesn\'t any animation data'
    packed_writer = PackedWriter()
    bpy_act = bpy_obj.animation_data.action
    packed_writer.puts('')
    frange = bpy_act.frame_range
    packed_writer.putf('II', int(frange[0]), int(frange[1]))
    fps = bpy_act.xray.fps
    packed_writer.putf('fH', fps, 5)
    if bpy_act.xray.autobake_effective(bpy_obj):
        baked_action = bpy.data.actions.new('')
        try:
            _bake_to_action(bpy_obj, baked_action, frange)
            _export_action_data(packed_writer, bpy_act.xray, baked_action.fcurves)
        finally:
            bpy.data.actions.remove(baked_action, do_unlink=True)
    else:
        assert bpy_obj.rotation_mode == 'YXZ', 'Animation: rotation mode must be \'YXZ\''
        _export_action_data(packed_writer, bpy_act.xray, bpy_act.fcurves)
    chunked_writer.put(Chunks.MAIN, packed_writer)


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


def _export_action_data(pkw, xray, fcurves):
    for i in range(6):
        fcurve = fcurves[(0, 2, 1, 5, 3, 4)[i]]
        koef = (1, 1, 1, -1, -1, -1)[i]
        epsilon = EPSILON
        if xray.autobake_custom_refine:
            epsilon = xray.autobake_refine_location if i < 3 else xray.autobake_refine_rotation
        export_envelope(
            pkw, fcurve,
            xray.fps, koef,
            epsilon=epsilon
        )


def export_file(bpy_obj, fpath):
    with io.open(fpath, 'wb') as file:
        writer = ChunkedWriter()
        _export(bpy_obj, writer)
        file.write(writer.data)
