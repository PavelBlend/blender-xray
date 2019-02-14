import math

import bgl


def matrix_to_buffer(matrix):
    buff = bgl.Buffer(bgl.GL_FLOAT, len(matrix.row) * len(matrix.col))
    for i, row in enumerate(matrix.row):
        buff[4 * i:4 * i + 4] = row
    return buff


def draw_wire_cube(hsx, hsy, hsz):
    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glVertex3f(-hsx, -hsy, -hsz)
    bgl.glVertex3f(+hsx, -hsy, -hsz)
    bgl.glVertex3f(+hsx, +hsy, -hsz)
    bgl.glVertex3f(-hsx, +hsy, -hsz)
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glVertex3f(-hsx, -hsy, +hsz)
    bgl.glVertex3f(+hsx, -hsy, +hsz)
    bgl.glVertex3f(+hsx, +hsy, +hsz)
    bgl.glVertex3f(-hsx, +hsy, +hsz)
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex3f(-hsx, -hsy, -hsz)
    bgl.glVertex3f(-hsx, -hsy, +hsz)
    bgl.glVertex3f(+hsx, -hsy, -hsz)
    bgl.glVertex3f(+hsx, -hsy, +hsz)
    bgl.glVertex3f(+hsx, +hsy, -hsz)
    bgl.glVertex3f(+hsx, +hsy, +hsz)
    bgl.glVertex3f(-hsx, +hsy, -hsz)
    bgl.glVertex3f(-hsx, +hsy, +hsz)
    bgl.glEnd()


# pylint: disable=C0103
def gen_circle(radius, num_segments, fconsumer):
    theta = 2.0 * math.pi / num_segments
    cos_th, sin_th = math.cos(theta), math.sin(theta)
    x, y = radius, 0
    for _ in range(num_segments):
        fconsumer(x, y)
        _ = x
        x = x * cos_th - y * sin_th
        y = _ * sin_th + y * cos_th


# pylint: disable=C0103
def gen_limit_circle(axis, rotate, radius, num_segments, fconsumer, color, min_limit, max_limit):
    theta = 2.0 * math.pi / num_segments
    cos_th, sin_th = math.cos(theta), math.sin(theta)
    cos_min = math.cos(math.radians(min_limit))
    sin_min = math.sin(math.radians(min_limit))

    bgl.glLineWidth(2)
    grey_color = (0.5, 0.5, 0.5, 0.8)

    rotate_point_x = None
    rotate_point_y = None

    # positive arc
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    x, y = radius, 0
    for _ in range(0, 181):
        if _ > max_limit or _ <= min_limit:
            bgl.glColor4f(*grey_color)
        else:
            bgl.glColor4f(*color)
        fconsumer(-x, -y)

        if rotate >= 0.0:
            rotate_int = abs(int(round(rotate, 0)))
            if 0 < rotate_int <= 180:
                if rotate_int == _:
                    rotate_point_x = -x
                    rotate_point_y = -y
            elif rotate_int == 0:
                rotate_point_x = -radius
                rotate_point_y = 0
            else:
                rotate_point_x = radius
                rotate_point_y = 0

        _ = x
        x = x * cos_th - y * sin_th
        y = _ * sin_th + y * cos_th
    bgl.glEnd()

    # negative arc
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    x, y = radius, 0
    for _ in range(0, 181):
        if -_ >= max_limit or -_ < min_limit:
            bgl.glColor4f(*grey_color)
        else:
            bgl.glColor4f(*color)
        fconsumer(-x, y)

        if rotate < 0.0:
            rotate_int = abs(int(round(rotate, 0)))
            if 0 < rotate_int <= 180:
                if rotate_int == _:
                    rotate_point_x = -x
                    rotate_point_y = y
            elif rotate_int > 180:
                rotate_point_x = radius
                rotate_point_y = 0

        _ = x
        x = x * cos_th - y * sin_th
        y = _ * sin_th + y * cos_th
    bgl.glEnd()

    bgl.glPointSize(6)
    bgl.glColor4f(1.0, 1.0, 0.0, 1.0)
    bgl.glBegin(bgl.GL_POINTS)
    if rotate_point_x is not None and rotate_point_y is not None:
        fconsumer(rotate_point_x, rotate_point_y)
    bgl.glEnd()


def draw_joint_limits(rotate, min_limit, max_limit, axis):
    colors = {
        'X': (1.0, 0.0, 0.0, 1.0),
        'Y': (0.0, 1.0, 0.0, 1.0),
        'Z': (0.0, 0.0, 1.0, 1.0)
    }
    draw_functions = {
        'X': (lambda x, y: bgl.glVertex3f(0, -x, y)),
        'Y': (lambda x, y: bgl.glVertex3f(-y, 0, x)),
        'Z': (lambda x, y: bgl.glVertex3f(-x, -y, 0))
    }
    color = colors[axis]
    radius = 0.1
    num_segments = 360
    gen_limit_circle(
        axis, rotate, radius, num_segments, draw_functions[axis], color,
        round(min_limit, 0), round(max_limit, 0)
    )


def draw_wire_sphere(radius, num_segments):
    bgl.glBegin(bgl.GL_LINE_LOOP)
    gen_circle(radius, num_segments, lambda x, y: bgl.glVertex3f(x, y, 0))
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_LOOP)
    gen_circle(radius, num_segments, lambda x, y: bgl.glVertex3f(0, x, y))
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_LOOP)
    gen_circle(radius, num_segments, lambda x, y: bgl.glVertex3f(y, 0, x))
    bgl.glEnd()


def draw_wire_cylinder(radius, half_height, num_segments):
    bgl.glBegin(bgl.GL_LINE_LOOP)
    gen_circle(radius, num_segments, lambda x, y: bgl.glVertex3f(x, -half_height, y))
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_LOOP)
    gen_circle(radius, num_segments, lambda x, y: bgl.glVertex3f(x, +half_height, y))
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex3f(-radius, -half_height, 0)
    bgl.glVertex3f(-radius, +half_height, 0)
    bgl.glVertex3f(+radius, -half_height, 0)
    bgl.glVertex3f(+radius, +half_height, 0)
    bgl.glVertex3f(0, -half_height, -radius)
    bgl.glVertex3f(0, +half_height, -radius)
    bgl.glVertex3f(0, -half_height, +radius)
    bgl.glVertex3f(0, +half_height, +radius)
    bgl.glEnd()

def draw_cross(size):
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex3f(-size, 0, 0)
    bgl.glVertex3f(+size, 0, 0)
    bgl.glVertex3f(0, -size, 0)
    bgl.glVertex3f(0, +size, 0)
    bgl.glVertex3f(0, 0, -size)
    bgl.glVertex3f(0, 0, +size)
    bgl.glEnd()
