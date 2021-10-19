# blender modules
import bpy

# addon modules
from . import fmt
from .. import log
from .. import utils
from .. import text
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
    packed_writer.putf('<fH', fps, fmt.MOTION_VERSION_5)
    autobake = bpy_act.xray.autobake_effective(bpy_obj)
    rot_mode = bpy_obj.rotation_mode
    if autobake or rot_mode != 'YXZ':
        if rot_mode != 'YXZ':
            log.warn(
                text.warn.anm_rot_mode,
                object=bpy_obj.name,
                rotation_mode=rot_mode
            )
        baked_action = bpy.data.actions.new('!-temp_anm_export')
        try:
            _bake_to_action(bpy_obj, baked_action, frange)
            _export_action_data(
                packed_writer,
                bpy_act.xray,
                baked_action.fcurves
            )
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
        loc = 'location'
        rot = 'rotation_euler'
        fc_trn = [
            action.fcurves.new(loc, index=0, action_group=group_name),
            action.fcurves.new(loc, index=1, action_group=group_name),
            action.fcurves.new(loc, index=2, action_group=group_name),
        ]
        fc_rot = [
            action.fcurves.new(rot, index=0, action_group=group_name),
            action.fcurves.new(rot, index=1, action_group=group_name),
            action.fcurves.new(rot, index=2, action_group=group_name)
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
                key_loc = fc_trn[i].keyframe_points.insert(frm, trn[i])
                key_loc.interpolation = 'LINEAR'
                key_rot = fc_rot[i].keyframe_points.insert(frm, rot[i])
                key_rot.interpolation = 'LINEAR'
    finally:
        bpy.context.scene.frame_set(old_frame)


def _export_action_data(pkw, xray, fcurves):
    location_curves = []
    rotation_curves = []
    for fcurve in fcurves:
        if fcurve.data_path == 'location':
            location_curves.append(fcurve.array_index)
        elif fcurve.data_path == 'rotation_euler':
            rotation_curves.append(fcurve.array_index)
    axis_keys = {0: 'X', 1: 'Y', 2: 'Z'}
    errors = []
    for i in range(3):
        if not (i in location_curves):
            errors.append('loc' + axis_keys[i])
        if not (i in rotation_curves):
            errors.append('rot' + axis_keys[i])
    if errors:
        message = ' '.join(errors)
        raise utils.AppError(
            text.error.anm_no_keys,
            log.props(channels=message)
        )
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
