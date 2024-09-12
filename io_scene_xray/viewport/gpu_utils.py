# standart modules
import math

# blender modules
import gpu

# addon modules
from . import const
from .. import utils

if utils.version.IS_28:
    # blender 2.8+ modules
    import gpu_extras.batch


ALPHA_COEF = 0.2


def gen_arc(
        radius, start, end, num_segments,
        fconsumer, indices, close=False
    ):

    theta = (end - start) / num_segments
    cos_th, sin_th = math.cos(theta), math.sin(theta)
    x, y = radius * math.cos(start), radius * math.sin(start)
    if indices:
        start_index = indices[-1][-1] + 1
    else:
        start_index = 0
    index = 0
    for _ in range(num_segments):
        fconsumer(x, y)
        indices.append(
            (start_index + index, start_index + index + 1)
        )
        index += 1
        _ = x
        x = x * cos_th - y * sin_th
        y = _ * sin_th + y * cos_th
    if close:
        fconsumer(x, y)


def gen_circle(radius, num_segments, fconsumer, indices):
    gen_arc(
        radius, 0, 2.0 * math.pi, num_segments,
        fconsumer, indices, close=True
    )


def draw_cube(half_size_x, half_size_y, half_size_z, color):
    coords = (
        (-half_size_x, -half_size_y, -half_size_z),
        (+half_size_x, -half_size_y, -half_size_z),
        (+half_size_x, +half_size_y, -half_size_z),
        (-half_size_x, +half_size_y, -half_size_z),

        (-half_size_x, -half_size_y, +half_size_z),
        (+half_size_x, -half_size_y, +half_size_z),
        (+half_size_x, +half_size_y, +half_size_z),
        (-half_size_x, +half_size_y, +half_size_z),
    )
    lines = (
        (0, 1), (1, 2),
        (2, 3), (3, 7),
        (2, 6), (1, 5),
        (0, 4), (4, 5),
        (5, 6), (6, 7),
        (4, 7), (0, 3)
    )
    faces = (
        (2, 0, 3),
        (2, 1, 0),
        (6, 4, 5),
        (6, 7, 4),
        (5, 0, 1),
        (5, 2, 6),
        (7, 2, 3),
        (4, 3, 0),
        (5, 4, 0),
        (5, 1, 2),
        (7, 6, 2),
        (4, 7, 3)
    )

    # solid cube
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'TRIS',
        {'pos': coords},
        indices=faces
    )
    shader.bind()
    shader.uniform_float('color', [*color[0 : 3], color[3] * ALPHA_COEF])
    batch.draw(shader)

    # wire cube
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'LINES',
        {'pos': coords},
        indices=lines
    )
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)


def draw_sphere(radius, num_segments, color):
    coords = []
    lines = []
    faces = []

    # generate vertex coordinates
    for i in range(num_segments + 1):
        theta = math.pi * i / num_segments
        for j in range(num_segments):
            phi = 2 * math.pi * j / num_segments
            x = radius * math.sin(theta) * math.cos(phi)
            y = radius * math.sin(theta) * math.sin(phi)
            z = radius * math.cos(theta)
            coords.append((x, y, z))

    # generate indices
    for i in range(num_segments):
        for j in range(num_segments):
            next_i = (i + 1)
            next_j = (j + 1) % num_segments

            current = i * num_segments + j
            next_lon = i * num_segments + next_j
            next_lat = next_i * num_segments + j
            next_lat_lon = next_i * num_segments + next_j

            # generate face indices
            if i != num_segments - 1:
                faces.append((current, next_lat, next_lat_lon))
            if i != 0:
                faces.append((current, next_lat_lon, next_lon))

            # generate wire indices
            if i == num_segments // 2:
                lines.append((current, next_lon))
            if j == num_segments // 2 or j == 0:
                lines.append((current, next_lat))
            if j == num_segments // 4 or j == num_segments // 4 * 3:
                lines.append((current, next_lat))

    # solid
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'TRIS',
        {'pos': coords},
        indices=faces
    )
    shader.bind()
    shader.uniform_float('color', [*color[0 : 3], color[3] * ALPHA_COEF])
    batch.draw(shader)

    # wire sphere
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'LINES',
        {'pos': coords},
        indices=lines
    )
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)


def draw_cylinder(radius, half_height, num_segments, color):
    coords = []
    lines = []
    gen_circle(
        radius,
        num_segments,
        lambda x, y: coords.append((x, -half_height, y)),
        lines
    )
    gen_circle(
        radius,
        num_segments,
        lambda x, y: coords.append((x, +half_height, y)),
        lines
    )

    faces = []

    bottom_start = 0
    top_start = num_segments + 1

    # bottom and top faces
    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        faces.append((bottom_start, bottom_start + next_i, bottom_start + i))
        faces.append((top_start, top_start + i, top_start + next_i))

    # side faces
    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        faces.append((bottom_start + i, top_start + i, bottom_start + next_i))
        faces.append((top_start + i, top_start + next_i, bottom_start + next_i))

    coords.extend([
        (-radius, -half_height, 0),
        (-radius, +half_height, 0),
        (+radius, -half_height, 0),
        (+radius, +half_height, 0),
        (0, -half_height, -radius),
        (0, +half_height, -radius),
        (0, -half_height, +radius),
        (0, +half_height, +radius)
    ])
    start_index = lines[-1][-1] + 1
    for i in range(start_index, start_index + 8, 2):
        lines.extend((
            (i, i + 1),
            (i +1, i)
        ))

    # solid cylinder
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'TRIS',
        {'pos': coords},
        indices=faces
    )
    shader.bind()
    shader.uniform_float('color', [*color[0 : 3], color[3] * ALPHA_COEF])
    batch.draw(shader)

    # wire cylinder
    shader = utils.draw.get_shader()
    batch = gpu_extras.batch.batch_for_shader(
        shader,
        'LINES',
        {'pos': coords},
        indices=lines
    )
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)


def draw_cross(size, color):
    coords = (
        (-size, 0, 0),
        (+size, 0, 0),
        (0, -size, 0),
        (0, +size, 0),
        (0, 0, -size),
        (0, 0, +size)
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
            gen_arc(
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
    gen_arc(radius, rotate, rotate + 1, 1, fconsumer, indices, close=False)

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
