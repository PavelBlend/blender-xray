import bgl
import math


def matrix_to_buffer(matrix):
    mb = bgl.Buffer(bgl.GL_FLOAT, len(matrix.row) * len(matrix.col))
    for i, r in enumerate(matrix.row):
        mb[4 * i:4 * i + 4] = r
    return mb


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


def gen_circle(radius, num_segments, fconsumer):
    theta = 2.0 * math.pi / num_segments
    cos_th, sin_th = math.cos(theta), math.sin(theta)
    x, y = radius, 0
    for i in range(num_segments):
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


def draw_wire_cylinder(radius, hh, num_segments):
    bgl.glBegin(bgl.GL_LINE_LOOP)
    gen_circle(radius, num_segments, lambda x, y: bgl.glVertex3f(x, -hh, y))
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_LOOP)
    gen_circle(radius, num_segments, lambda x, y: bgl.glVertex3f(x, +hh, y))
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex3f(-radius, -hh, 0)
    bgl.glVertex3f(-radius, +hh, 0)
    bgl.glVertex3f(+radius, -hh, 0)
    bgl.glVertex3f(+radius, +hh, 0)
    bgl.glVertex3f(0, -hh, -radius)
    bgl.glVertex3f(0, +hh, -radius)
    bgl.glVertex3f(0, -hh, +radius)
    bgl.glVertex3f(0, +hh, +radius)
    bgl.glEnd()
