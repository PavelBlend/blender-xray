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
from .. import xray_io


DISPLAY_SIZE = 0.5


class ImportAnmContext(contexts.ImportContext):
    def __init__(self):
        super().__init__()
        self.camera_animation = None


@log.with_context('import-anm-path')
def _import(fpath, creader, context):
    log.update(file=fpath)
    warn_list = []
    chunk_data = creader.next(fmt.Chunks.MAIN, no_error=True)
    if chunk_data is None:
        raise utils.AppError(
            text.error.anm_has_no_chunk,
            log.props(
                file=os.path.basename(fpath),
                path=fpath
            )
        )
    preader = xray_io.PackedReader(chunk_data)
    name = preader.gets()
    _fr = preader.getf('<2I')
    fps, ver = preader.getf('<fH')
    if ver != 5:
        raise utils.AppError(
            text.error.anm_unsupport_ver,
            log.props(
                file=os.path.basename(fpath),
                path=fpath,
                version=ver
            )
        )
    if not name:
        name = os.path.basename(fpath)
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
        display_type = 'SPHERE'
        if version_utils.IS_28:
            bpy_obj.empty_display_type = display_type
        else:
            bpy_obj.empty_draw_type = display_type
    if version_utils.IS_28:
        bpy_obj.empty_display_size = DISPLAY_SIZE
    else:
        bpy_obj.empty_draw_size = DISPLAY_SIZE
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
    for i in range(6):
        fcurve = fcs[(0, 2, 1, 5, 3, 4)[i]]
        koef = (1, 1, 1, -1, -1, -1)[i]
        use_interpolate = xray_envelope.import_envelope(
            preader,
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


def import_file(fpath, context):
    data = utils.read_file(fpath)
    chunked_reader = xray_io.ChunkedReader(data)
    _import(fpath, chunked_reader, context)
