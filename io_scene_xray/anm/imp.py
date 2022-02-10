# standart modules
import os
import math

# blender modules
import bpy

# addon modules
from . import fmt
from .. import contexts
from .. import text
from .. import utils
from .. import log
from .. import xray_envelope
from .. import version_utils
from .. import ie_utils
from .. import xray_io


DISPLAY_SIZE = 0.5


class ImportAnmContext(contexts.ImportContext):
    def __init__(self):
        super().__init__()
        self.camera_animation = None


def _import(file_path, creader, context):
    warn_list = []
    chunk_data = creader.next(fmt.Chunks.MAIN, no_error=True)
    if chunk_data is None:
        raise utils.AppError(
            text.error.anm_has_no_chunk,
            log.props(
                file=os.path.basename(file_path),
                path=file_path
            )
        )
    preader = xray_io.PackedReader(chunk_data)
    name = preader.gets()
    _fr = preader.getf('<2I')
    fps, ver = preader.getf('<fH')
    if not ver in fmt.MOTION_SUPPORTED_VERSIONS:
        raise utils.AppError(
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
    if context.camera_animation:
        bpy_cam = bpy.data.objects.new(
            name + '.camera',
            bpy.data.cameras.new(name)
        )
        bpy_cam.parent = bpy_obj
        bpy_cam.rotation_euler = (math.pi / 2, 0, 0)
        version_utils.link_object(bpy_cam)
    else:
        version_utils.set_empty_draw_type(bpy_obj, 'SPHERE')
    version_utils.set_empty_draw_size(bpy_obj, DISPLAY_SIZE)
    version_utils.link_object(bpy_obj)
    action = bpy.data.actions.new(name=name)
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
        use_interpolate = xray_envelope.import_envelope(
            preader,
            ver,
            fcurve,
            fps,
            koef,
            name,
            warn_list,
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
    for (shapes, replacement, name) in set(warn_list):
        keys_count = warn_list.count((shapes, replacement, name))
        log.warn(
            text.warn.anm_unsupport_shape,
            shapes=shapes,
            replacement=replacement,
            filename=name,
            keys_count=keys_count
        )


@log.with_context('import-anm-path')
def import_file(context):
    file_path = context.filepath
    log.update(file=file_path)
    ie_utils.check_file_exists(file_path)
    data = utils.read_file(file_path)
    chunked_reader = xray_io.ChunkedReader(data)
    _import(file_path, chunked_reader, context)
