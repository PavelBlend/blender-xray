# addon modules
from . import gl_utils
from . import gpu_utils
from . import settings
from .. import version_utils


def draw_cube(half_size_x, half_size_y, half_size_z, color=None):
    if version_utils.IS_28:
        gpu_utils.draw_wire_cube(half_size_x, half_size_y, half_size_z, color)
    else:
        gl_utils.draw_wire_cube(half_size_x, half_size_y, half_size_z)


def draw_sphere(radius, num_segments, color=None):
    if version_utils.IS_28:
        gpu_utils.draw_wire_sphere(radius, num_segments, color)
    else:
        gl_utils.draw_wire_sphere(radius, num_segments)


def draw_wire_cylinder(radius, half_height, num_segments, color=None):
    if version_utils.IS_28:
        gpu_utils.draw_wire_cylinder(radius, half_height, num_segments, color)
    else:
        gl_utils.draw_wire_cylinder(radius, half_height, num_segments)


def draw_cross(size, color=None):
    if version_utils.IS_28:
        gpu_utils.draw_cross(size, color)
    else:
        gl_utils.draw_cross(size)


def get_draw_joint_limits():
    if version_utils.IS_28:
        return gpu_utils.draw_joint_limits
    else:
        return gl_utils.draw_joint_limits
