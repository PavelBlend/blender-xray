# blender modules
import bpy

# addon modules
from . import gl_utils
from . import gpu_utils
from . import const
from . import geom
from .. import utils


def draw_cube(half_size_x, half_size_y, half_size_z, color, alpha_coef):
    if utils.version.IS_28:
        gpu_utils.draw_cube(half_size_x, half_size_y, half_size_z, color, alpha_coef)
    else:
        gl_utils.draw_cube(half_size_x, half_size_y, half_size_z, color, alpha_coef)


def draw_sphere(radius, num_segments, color, alpha_coef):
    if utils.version.IS_28:
        gpu_utils.draw_sphere(radius, num_segments, color, alpha_coef)
    else:
        gl_utils.draw_sphere(radius, num_segments, color, alpha_coef)


def draw_cylinder(radius, half_height, num_segments, color, alpha_coef):
    if utils.version.IS_28:
        gpu_utils.draw_cylinder(radius, half_height, num_segments, color, alpha_coef)
    else:
        gl_utils.draw_cylinder(radius, half_height, num_segments, color, alpha_coef)


def draw_cross(size, color=None):
    if utils.version.IS_28:
        gpu_utils.draw_cross(size, color)
    else:
        gl_utils.draw_cross(size)


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


def try_draw(obj):
    if obj.data:
        xray = getattr(obj.data, 'xray', None)
        if xray and hasattr(xray, 'ondraw_postview'):
            xray.ondraw_postview(obj)


def overlay_view_3d():
    for obj in bpy.data.objects:
        try_draw(obj)


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
