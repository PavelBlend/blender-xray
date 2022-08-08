# blender modules
import bpy

# addon modules
from . import fmt
from .. import log
from .. import utils
from .. import contexts
from .. import text
from .. import xray_io
from .. import xray_envelope


class ExportAnmContext(contexts.ExportContext):
    def __init__(self):
        super().__init__()
        self.format_version = None
        self.active_object = None


@log.with_context(name='object')
def _export(export_context, chunked_writer):
    packed_writer = xray_io.PackedWriter()
    bpy_obj = export_context.active_object
    log.update(object=bpy_obj.name)
    bpy_act = bpy_obj.animation_data.action
    packed_writer.puts('')
    frange = bpy_act.frame_range
    packed_writer.putf('<2I', int(frange[0]), int(frange[1]))
    fps = bpy_act.xray.fps
    ver = int(export_context.format_version)
    packed_writer.putf('<fH', fps, ver)
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
                ver,
                bpy_act.xray,
                baked_action.fcurves
            )
        finally:
            utils.version.remove_action(baked_action)
    else:
        _export_action_data(
            packed_writer,
            ver,
            bpy_act.xray,
            bpy_act.fcurves
        )
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
            for axis in range(3):
                key_loc = fc_trn[axis].keyframe_points.insert(frm, trn[axis])
                key_loc.interpolation = 'LINEAR'
                key_rot = fc_rot[axis].keyframe_points.insert(frm, rot[axis])
                key_rot.interpolation = 'LINEAR'
    finally:
        bpy.context.scene.frame_set(old_frame)


def _export_action_data(pkw, ver, xray, fcurves):
    location_curves = []
    rotation_curves = []
    for fcurve in fcurves:
        if fcurve.data_path == 'location':
            location_curves.append(fcurve.array_index)
        elif fcurve.data_path == 'rotation_euler':
            rotation_curves.append(fcurve.array_index)
    axis_keys = {0: 'X', 1: 'Y', 2: 'Z'}
    errors = []
    for axis in range(3):
        if not (axis in location_curves):
            errors.append('loc' + axis_keys[axis])
        if not (axis in rotation_curves):
            errors.append('rot' + axis_keys[axis])
    if errors:
        message = ' '.join(errors)
        raise log.AppError(
            text.error.anm_no_keys,
            log.props(channels=message)
        )
    for curve_index in range(6):
        fcurve = fcurves[(0, 2, 1, 5, 3, 4)[curve_index]]
        koef = (1, 1, 1, -1, -1, -1)[curve_index]
        epsilon = utils.motion.EPSILON
        if xray.autobake_custom_refine:
            if curve_index < 3:
                epsilon = xray.autobake_refine_location
            else:
                epsilon = xray.autobake_refine_rotation
        xray_envelope.export_envelope(
            pkw,
            ver,
            fcurve,
            xray.fps,
            koef,
            epsilon=epsilon
        )


@log.with_context('export-anm')
def export_file(export_context):
    log.update(file=export_context.filepath)
    writer = xray_io.ChunkedWriter()
    _export(export_context, writer)
    utils.save_file(export_context.filepath, writer)
