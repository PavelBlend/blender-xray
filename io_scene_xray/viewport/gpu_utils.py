# standart modules
import math

# blender modules
import gpu

# addon modules
from . import const
from . import geom
from .. import utils

if utils.version.IS_28:
    # blender 2.8+ modules
    import gpu_extras.batch


def draw_geom(coords, lines, faces, color_solid, color_wire):
    # solid geometry
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'TRIS',
        {'pos': coords},
        indices=faces
    )
    shader.bind()
    shader.uniform_float('color', color_solid)
    batch.draw(shader)

    # wire geometry
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'LINES',
        {'pos': coords},
        indices=lines
    )
    shader.bind()
    shader.uniform_float('color', color_wire)
    batch.draw(shader)


def draw_line(start, end, color):
    coords = (
        start,
        end
    )
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'LINES',
        {'pos': coords}
    )
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)


def gen_limit_circle(
        rotate, radius, num_segments,
        axis, color, min_limit, max_limit
    ):

    def gen_arc_vary(radius, start, end, indices):
        num_segs = math.ceil(
            num_segments * abs(end - start) / (math.pi * 2.0)
        )
        if num_segs:
            geom.gen_arc(
                radius, start, end, num_segs,
                fconsumer, indices, close=True
            )

    draw_functions = {
        'X': (lambda x, y: coords.append((0, -x, -y))),
        'Y': (lambda x, y: coords.append((-y, 0, -x))),
        'Z': (lambda x, y: coords.append((x, y, 0)))
    }
    fconsumer = draw_functions[axis]

    # draw min limit
    color_min = (color[0]*0.5, color[1]*0.5, color[2]*0.5, color[3])
    coords = []
    indices = []
    gen_arc_vary(radius, min_limit, 0, indices)
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'LINES',
        {'pos': coords, },
        indices=indices
    )
    shader.bind()
    shader.uniform_float('color', color_min)
    batch.draw(shader)

    # draw max limit
    coords = []
    indices = []
    gen_arc_vary(radius, 0, max_limit, indices)
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'LINES',
        {'pos': coords, },
        indices=indices
    )
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)

    # draw circle
    coords = []
    indices = []
    gen_arc_vary(radius, max_limit, 2.0 * math.pi + min_limit, indices)
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'LINES',
        {'pos': coords, },
        indices=indices
    )
    shader.bind()
    shader.uniform_float('color', const.GREY_COLOR)
    batch.draw(shader)

    # draw current rotation point
    coords = []
    indices = []
    geom.gen_arc(radius, rotate, rotate + 1, 1, fconsumer, indices, close=False)

    gpu.state.point_size_set(const.POINT_SIZE)

    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'POINTS',
        {'pos': coords, }
    )
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)


def draw_joint_limits(rotate, min_limit, max_limit, axis, radius):
    color = const.AXIS_COLORS[axis]
    if axis != 'Z':
        rotate = -rotate
    gen_limit_circle(
        rotate, radius,
        const.JOINT_LIMITS_CIRCLE_SEGMENTS_COUNT,
        axis, color,
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
        'Z',
        color,
        rotation_min,
        rotation_max
    )


def draw_slider_slide_limits(slide_min, slide_max, color):
    start = (0, 0, slide_min)
    end = (0, 0, slide_max)
    draw_line(start, end, color)
