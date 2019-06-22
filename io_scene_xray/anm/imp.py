import io
import math
import os.path

import bpy

from ..xray_io import ChunkedReader, PackedReader
from .fmt import Chunks
from ..xray_envelope import import_envelope


class ImportContext:
    def __init__(self, camera_animation=False):
        self.camera_animation = camera_animation


def _import(fpath, creader, context):
    for cid, data in creader:
        if cid == Chunks.MAIN:
            preader = PackedReader(data)
            name = preader.gets()
            _fr = preader.getf('II')
            fps, ver = preader.getf('fH')
            if ver != 5:
                raise Exception('unsupported anm version: ' + str(ver))
            if not name:
                name = os.path.basename(fpath)
            bpy_obj = bpy.data.objects.new(name, None)
            bpy_obj.rotation_mode = 'YXZ'
            if context.camera_animation:
                bpy_cam = bpy.data.objects.new(name + '.camera', bpy.data.cameras.new(name))
                bpy_cam.parent = bpy_obj
                bpy_cam.rotation_euler = (math.pi / 2, 0, 0)
                bpy.context.scene.objects.link(bpy_cam)
            else:
                bpy_obj.empty_draw_type = 'SPHERE'
            bpy_obj.empty_draw_size = 0.5
            bpy.context.scene.objects.link(bpy_obj)
            action = bpy.data.actions.new(name=name)
            action.xray.fps = fps
            bpy_obj.animation_data_create().action = action
            fcs = (
                action.fcurves.new('location', index=0, action_group=name),
                action.fcurves.new('location', index=1, action_group=name),
                action.fcurves.new('location', index=2, action_group=name),
                action.fcurves.new('rotation_euler', index=0, action_group=name),
                action.fcurves.new('rotation_euler', index=1, action_group=name),
                action.fcurves.new('rotation_euler', index=2, action_group=name)
            )
            for i in range(6):
                fcurve = fcs[(0, 2, 1, 5, 3, 4)[i]]
                koef = (1, 1, 1, -1, -1, -1)[i]
                import_envelope(preader, fcurve, fps, koef)


def import_file(fpath, context):
    with io.open(fpath, 'rb') as file:
        _import(fpath, ChunkedReader(file.read()), context)
