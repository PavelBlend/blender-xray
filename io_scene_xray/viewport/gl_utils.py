# standart modules
import math

# blender modules
import bgl

# addon modules
from . import const
from . import geom


axis_draw_functions = {
    'X': (lambda x, y: bgl.glVertex3f(0, -x, -y)),
    'Y': (lambda x, y: bgl.glVertex3f(-y, 0, -x)),
    'Z': (lambda x, y: bgl.glVertex3f(x, y, 0))
}


def matrix_to_buffer(matrix):
    buff = bgl.Buffer(bgl.GL_FLOAT, len(matrix.row) * len(matrix.col))
    for row_index, row in enumerate(matrix.row):
        buff[4 * row_index : 4 * row_index + 4] = row
    return buff


# pylint: disable=C0103
def draw_arc(radius, start, end, num_segments, fconsumer, close=False):
    theta = (end - start) / num_segments
    cos_th, sin_th = math.cos(theta), math.sin(theta)
    x, y = radius * math.cos(start), radius * math.sin(start)
    for _ in range(num_segments):
        fconsumer(x, y)
        _ = x
        x = x * cos_th - y * sin_th
        y = _ * sin_th + y * cos_th
    if close:
        fconsumer(x, y)


def draw_geom(coords, lines, faces, color_solid, color_wire):
    # solid geometry
    if faces:
        bgl.glColor4f(*color_solid)
        bgl.glBegin(bgl.GL_TRIANGLES)
        for face in faces:
            for vertex in face:
                bgl.glVertex3f(*coords[vertex])
        bgl.glEnd()

    # wire geometry
    if lines:
        bgl.glColor4f(*color_wire)
        bgl.glBegin(bgl.GL_LINES)
        for line in lines:
            for vertex in line:
                bgl.glVertex3f(*coords[vertex])
        bgl.glEnd()


# pylint: disable=C0103
def gen_limit_circle(
        rotate, radius, num_segments,
        fconsumer, color,
        min_limit, max_limit
    ):

    def gen_arc_vary(radius, start, end):
        num_segs = math.ceil(
            num_segments * abs(end - start) / (math.pi * 2.0)
        )
        if num_segs:
            draw_arc(radius, start, end, num_segs, fconsumer, close=True)

    bgl.glLineWidth(2)
    bgl.glBegin(bgl.GL_LINE_STRIP)

    # draw min limit
    color_min = (color[0]*0.5, color[1]*0.5, color[2]*0.5, color[3])
    bgl.glColor4f(*color_min)
    gen_arc_vary(radius, min_limit, 0)

    # draw max limit
    bgl.glColor4f(*color)
    gen_arc_vary(radius, 0, max_limit)

    # draw circle
    bgl.glColor4f(*const.GREY_COLOR)
    gen_arc_vary(radius, max_limit, 2.0 * math.pi + min_limit)

    bgl.glEnd()

    bgl.glPointSize(const.POINT_SIZE)
    bgl.glColor4f(*color)
    bgl.glBegin(bgl.GL_POINTS)
    draw_arc(radius, rotate, rotate + 1, 1, fconsumer)
    bgl.glEnd()


def draw_joint_limits(rotate, min_limit, max_limit, axis, radius):
    color = const.AXIS_COLORS[axis]
    if axis != 'Z':
        rotate = -rotate
    gen_limit_circle(
        rotate, radius,
        const.JOINT_LIMITS_CIRCLE_SEGMENTS_COUNT,
        axis_draw_functions[axis], color,
        min_limit, max_limit
    )


def draw_slider_rotation_limits(
        rotation,
        rotation_min,
        rotation_max,
        radius
    ):
    color = const.AXIS_COLORS['Z']
    gen_limit_circle(
        rotation,
        radius,
        const.JOINT_LIMITS_CIRCLE_SEGMENTS_COUNT,
        axis_draw_functions['Z'],
        color,
        rotation_min,
        rotation_max
    )


def draw_slider_slide_limits(slide_min, slide_max, color):
    start = (0, 0, slide_min)
    end = (0, 0, slide_max)
    draw_line(start, end, color)


def draw_line(start, end, color):
    bgl.glBegin(bgl.GL_LINES)
    bgl.glColor4f(*color)
    bgl.glVertex3f(*start)
    bgl.glVertex3f(*end)
    bgl.glEnd()
