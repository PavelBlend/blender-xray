# blender modules
import bpy

# addon modules
from . import gl_utils
from . import gpu_utils
from . import const
from . import ctx
from . import geom
from .. import utils


def get_draw_joint_limits():
    if utils.version.IS_28:
        return gpu_utils.draw_joint_limits
    else:
        return gl_utils.draw_joint_limits


def get_draw_slider_rotation_limits():
    if utils.version.IS_28:
        return gpu_utils.draw_slider_rotation_limits
    else:
        return gl_utils.draw_slider_rotation_limits


def get_draw_slider_slide_limits():
    if utils.version.IS_28:
        return gpu_utils.draw_slider_slide_limits
    else:
        return gl_utils.draw_slider_slide_limits


def overlay_view_3d():
    context = ctx.DrawContext()

    # set opengl state for limits draw
    utils.draw.reset_gl_state()
    utils.draw.set_gl_line_width(const.LINE_WIDTH)

    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            obj.data.xray.ondraw_postview(obj, context)

    context.draw()


def register():
    overlay_view_3d.__handle = bpy.types.SpaceView3D.draw_handler_add(
        overlay_view_3d,
        (),
        'WINDOW',
        'POST_VIEW'
    )


def unregister():
    bpy.types.SpaceView3D.draw_handler_remove(
        overlay_view_3d.__handle,
        'WINDOW'
    )
