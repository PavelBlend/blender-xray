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
