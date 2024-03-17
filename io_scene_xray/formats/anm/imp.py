# standart modules
import os
import math

# blender modules
import bpy

# addon modules
from . import fmt
from .. import contexts
from .. import motions
from ... import text
from ... import utils
from ... import log
from ... import rw


DISPLAY_SIZE = 0.5


class ImportAnmContext(contexts.ImportContext):
    def __init__(self):
        super().__init__()
        self.camera_animation = None


def _import(file_path, creader, context):
    chunk_data = creader.next(fmt.Chunks.MAIN, error=False)
    if chunk_data is None:
        raise log.AppError(
            text.error.has_no_main_chunk,
            log.props(
                file=os.path.basename(file_path),
                path=file_path
            )
        )
    preader = rw.read.PackedReader(chunk_data)
    name = preader.gets()
    frame_start, frame_end = preader.getf('<2I')
    fps, ver = preader.getf('<fH')
    if not ver in fmt.MOTION_SUPPORTED_VERSIONS:
        raise log.AppError(
            text.error.anm_unsupport_ver,
            log.props(
                file=os.path.basename(file_path),
                path=file_path,
                version=ver
            )
        )
    if not name:
        name = os.path.basename(file_path)
    bpy_obj = bpy.data.objects.new(name, None)
    bpy_obj.rotation_mode = 'YXZ'
    utils.stats.created_obj()

    if context.camera_animation:
        camera = bpy.data.cameras.new(name)
        bpy_cam = bpy.data.objects.new(name + '.camera', camera)
        bpy_cam.parent = bpy_obj
        bpy_cam.rotation_euler = (math.pi / 2, 0, 0)
        camera.lens_unit = 'FOV'
        camera.sensor_fit = 'VERTICAL'
        camera.angle = math.radians(utils.obj.SOC_LEVEL_FOV)
        utils.version.link_object(bpy_cam)
        utils.stats.created_obj()
    else:
        utils.version.set_empty_draw_type(bpy_obj, 'SPHERE')

    utils.version.set_empty_draw_size(bpy_obj, DISPLAY_SIZE)
    utils.version.link_object(bpy_obj)
    action = bpy.data.actions.new(name=name)
    utils.stats.created_act()
    action.xray.fps = fps
    bpy_obj.animation_data_create().action = action
    loc = 'location'
    rot = 'rotation_euler'
    fcs = (
        action.fcurves.new(loc, index=0, action_group=name),
        action.fcurves.new(loc, index=1, action_group=name),
        action.fcurves.new(loc, index=2, action_group=name),
        action.fcurves.new(rot, index=0, action_group=name),
        action.fcurves.new(rot, index=1, action_group=name),
        action.fcurves.new(rot, index=2, action_group=name)
    )
    converted_warrning = False
    unique_shapes = set()
    for curve_index in range(6):
        fcurve = fcs[(0, 2, 1, 5, 3, 4)[curve_index]]
        koef = (1, 1, 1, -1, -1, -1)[curve_index]
        use_interpolate = motions.envelope.import_envelope(
            preader,
            ver,
            fcurve,
            fps,
            koef,
            name,
            unique_shapes
        )
        if use_interpolate:
            converted_warrning = True

    if converted_warrning:
        log.warn(
            text.warn.anm_conv_linear,
            anm_name=name,
            shapes=unique_shapes
        )

    return frame_start, frame_end


@log.with_context('import-anm')
@utils.stats.timer
def import_file(file_path, context):
    utils.stats.status('Import File', file_path)

    chunked_reader = rw.utils.get_file_reader(file_path, chunked=True)
    frame_start, frame_end = _import(file_path, chunked_reader, context)

    return frame_start, frame_end
