# standart modules
import math


def gen_arc(
        radius,
        start,
        end,
        num_segments,
        fconsumer,
        indices,
        close=False
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
        radius,
        0,
        2.0 * math.pi,
        num_segments,
        fconsumer,
        indices,
        close=True
    )


def gen_cube_geom(half_size_x, half_size_y, half_size_z):
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
    return coords, lines, faces


def gen_cylinder_geom(radius, half_height, num_segments):
    coords = []
    lines = []
    faces = []

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

    bottom_start = 0
    top_start = num_segments + 1

    # bottom and top faces
    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        faces.append((bottom_start, bottom_start + i, bottom_start + next_i))
        faces.append((top_start, top_start + next_i, top_start + i))

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

    return coords, lines, faces


def gen_sphere_geom(radius, num_segments):
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

    return coords, lines, faces
