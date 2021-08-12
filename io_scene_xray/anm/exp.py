# blender modules
import bpy

# addon modules
from . import fmt
from .. import log
from .. import utils
from .. import version_utils
from .. import xray_io
from .. import xray_envelope
from .. import motion_utils


def _export(bpy_obj, chunked_writer):
    packed_writer = xray_io.PackedWriter()
    bpy_act = bpy_obj.animation_data.action
    packed_writer.puts('')
    frange = bpy_act.frame_range
    packed_writer.putf('<2I', int(frange[0]), int(frange[1]))
    fps = bpy_act.xray.fps
    packed_writer.putf('<fH', fps, 5)
    autobake = bpy_act.xray.autobake_effective(bpy_obj)
    rot_mode = bpy_obj.rotation_mode
    if autobake or rot_mode != 'YXZ':
        if rot_mode != 'YXZ':
            log.warn(
                'Object "{}" has a rotation mode other than YXZ. '
                'Animation has been baked.'.format(bpy_obj.name),
                rotation_mode=rot_mode
            )
        baked_action = bpy.data.actions.new('!-temp_anm_export')
        try:
            _bake_to_action(bpy_obj, baked_action, frange)
            _export_action_data(packed_writer, bpy_act.xray, baked_action.fcurves)
        finally:
            if not version_utils.IS_277:
                bpy.data.actions.remove(baked_action, do_unlink=True)
            else:
                baked_action.user_clear()
                bpy.data.actions.remove(baked_action)
    else:
        _export_action_data(packed_writer, bpy_act.xray, bpy_act.fcurves)
    chunked_writer.put(fmt.Chunks.MAIN, packed_writer)


def _bake_to_action(bobject, action, frange):
    old_frame = bpy.context.scene.frame_current
    try:
        group_name = 'LocRot'
        fc_trn = [
            action.fcurves.new('location', index=0, action_group=group_name),
            action.fcurves.new('location', index=1, action_group=group_name),
            action.fcurves.new('location', index=2, action_group=group_name),
        ]
        fc_rot = [
            action.fcurves.new('rotation_euler', index=0, action_group=group_name),
            action.fcurves.new('rotation_euler', index=1, action_group=group_name),
            action.fcurves.new('rotation_euler', index=2, action_group=group_name)
        ]
        prev_rot = None
        for frm in range(int(frange[0]), int(frange[1]) + 1):
            bpy.context.scene.frame_set(frm)
            mat = bobject.matrix_world
            trn = mat.to_translation()
            rot = mat.to_euler('YXZ')
            if prev_rot:
                utils.smooth_euler(rot, prev_rot)
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
        epsilon = motion_utils.EPSILON
        if xray.autobake_custom_refine:
            if i < 3:
                epsilon = xray.autobake_refine_location
            else:
                epsilon = xray.autobake_refine_rotation
        xray_envelope.export_envelope(
            pkw,
            fcurve,
            xray.fps,
            koef,
            epsilon=epsilon
        )


def export_file(bpy_obj, fpath):
    writer = xray_io.ChunkedWriter()
    _export(bpy_obj, writer)
    utils.save_file(fpath, writer)
