# blender modules
import bpy

# addon modules
from . import fmt
from .. import contexts
from .. import motions
from ... import log
from ... import utils
from ... import text
from ... import rw


class ExportAnmContext(contexts.ExportContext):
    def __init__(self):
        super().__init__()
        self.format_version = None
        self.active_object = None


@log.with_context(name='object')
def _export(export_context, chunked_writer):
    bpy_obj = export_context.active_object
    log.update(object=bpy_obj.name)

    # name
    packed_writer = rw.write.PackedWriter()
    packed_writer.puts('')

    # frame range
    bpy_act = bpy_obj.animation_data.action
    frame_start = int(bpy_act.frame_range[0])
    frame_end = int(bpy_act.frame_range[1])
    packed_writer.putf('<2I', frame_start, frame_end)

    # fps
    fps = bpy_act.xray.fps
    packed_writer.putf('<f', fps)

    # version
    ver = int(export_context.format_version)
    packed_writer.putf('<H', ver)

    # export
    bake = False

    if bpy_act.xray.autobake_effective(bpy_obj):
        bake = True

    rot_mode = bpy_obj.rotation_mode
    if rot_mode != 'YXZ':
        bake = True
        log.warn(
            text.warn.anm_rot_mode,
            object=bpy_obj.name,
            rotation_mode=rot_mode
        )

    if bake:
        baked_action = bpy.data.actions.new('!-temp_anm_export')
        try:
            _bake_to_action(bpy_obj, baked_action, frame_start, frame_end)
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

    # writing chunk
    chunked_writer.put(fmt.Chunks.MAIN, packed_writer)


def _bake_to_action(obj, action, frame_start, frame_end):
    frame_cur = bpy.context.scene.frame_current

    try:
        # create f-curves
        group_name = 'LocRot'
        fcurves_loc = [
            action.fcurves.new(
                'location',
                index=axis,
                action_group=group_name
            )
            for axis in range(3)
        ]
        fcurves_rot = [
            action.fcurves.new(
                'rotation_euler',
                index=axis,
                action_group=group_name
            )
            for axis in range(3)
        ]

        # insert keyframes
        prev_rot = None
        for frame in range(frame_start, frame_end + 1):
            bpy.context.scene.frame_set(frame)

            # get transforms
            mat = obj.matrix_world
            obj_loc = mat.to_translation()
            obj_rot = mat.to_euler('YXZ')

            if prev_rot:
                utils.smooth_euler(obj_rot, prev_rot)
            prev_rot = obj_rot

            for axis in range(3):    # x, y, z
                # insert location keyframe
                key_loc = fcurves_loc[axis].keyframe_points.insert(
                    frame,
                    obj_loc[axis]
                )
                key_loc.interpolation = 'LINEAR'

                # insert rotation keyframe
                key_rot = fcurves_rot[axis].keyframe_points.insert(
                    frame,
                    obj_rot[axis]
                )
                key_rot.interpolation = 'LINEAR'

    finally:
        bpy.context.scene.frame_set(frame_cur)


axis_keys = {
    0: 'X',
    1: 'Y',
    2: 'Z'
}


def _export_action_data(packed_writer, ver, xray, fcurves):
    # collect fcurve axes
    loc_axes = []
    rot_axes = []

    for fcurve in fcurves:
        if fcurve.data_path == 'location':
            loc_axes.append(fcurve.array_index)

        elif fcurve.data_path == 'rotation_euler':
            rot_axes.append(fcurve.array_index)

    # search errors
    errors = []

    for axis in range(3):
        if axis not in loc_axes:
            errors.append('loc' + axis_keys[axis])

        if axis not in rot_axes:
            errors.append('rot' + axis_keys[axis])

    if errors:
        message = ' '.join(errors)
        raise log.AppError(
            text.error.anm_no_keys,
            log.props(channels=message)
        )

    # export
    for curve_index in range(6):
        fcurve = fcurves[(0, 2, 1, 5, 3, 4)[curve_index]]
        coef = (1, 1, 1, -1, -1, -1)[curve_index]

        epsilon = motions.utilites.EPSILON
        if xray.autobake_custom_refine:
            if curve_index < 3:
                epsilon = xray.autobake_refine_location
            else:
                epsilon = xray.autobake_refine_rotation

        motions.envelope.export_envelope(
            packed_writer,
            ver,
            fcurve,
            xray.fps,
            coef,
            epsilon=epsilon
        )


@log.with_context('export-anm')
@utils.stats.timer
def export_file(export_context):
    utils.stats.status('Export File', export_context.filepath)

    log.update(file=export_context.filepath)
    writer = rw.write.ChunkedWriter()
    _export(export_context, writer)
    rw.utils.save_file(export_context.filepath, writer)
