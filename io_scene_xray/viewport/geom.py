# standart modules
import math

# blender modules
import mathutils

# addon modules
from . import const


def gen_arc(
        radius,
        start,
        end,
        num_segments,
        fconsumer,
        indices,
        close=False,
        offset=0,
    ):

    theta = (end - start) / num_segments
    cos_th, sin_th = math.cos(theta), math.sin(theta)
    x, y = radius * math.cos(start), radius * math.sin(start)
    if indices and not offset:
        start_index = indices[-1][-1] + 1
    else:
        start_index = 0
    index = 0
    for _ in range(num_segments):
        fconsumer(x, y)
        indices.append(
            (start_index + index + offset, start_index + index + offset + 1)
        )
        index += 1
        _ = x
        x = x * cos_th - y * sin_th
        y = _ * sin_th + y * cos_th
    if close:
        fconsumer(x, y)


def gen_circle(radius, num_segments, fconsumer, indices, offset=0):
    gen_arc(
        radius,
        0,
        2.0 * math.pi,
        num_segments,
        fconsumer,
        indices,
        close=True,
        offset=offset
    )


def gen_cube_geom(mat, coords, lines, faces):
    offset = len(coords)
    coords.extend((
        mat @ mathutils.Vector((-1.0, -1.0, -1.0)),
        mat @ mathutils.Vector((+1.0, -1.0, -1.0)),
        mat @ mathutils.Vector((+1.0, +1.0, -1.0)),
        mat @ mathutils.Vector((-1.0, +1.0, -1.0)),

        mat @ mathutils.Vector((-1.0, -1.0, +1.0)),
        mat @ mathutils.Vector((+1.0, -1.0, +1.0)),
        mat @ mathutils.Vector((+1.0, +1.0, +1.0)),
        mat @ mathutils.Vector((-1.0, +1.0, +1.0)),
    ))
    lines.extend((
        (offset + 0, offset + 1), (offset + 1, offset + 2),
        (offset + 2, offset + 3), (offset + 3, offset + 7),
        (offset + 2, offset + 6), (offset + 1, offset + 5),
        (offset + 0, offset + 4), (offset + 4, offset + 5),
        (offset + 5, offset + 6), (offset + 6, offset + 7),
        (offset + 4, offset + 7), (offset + 0, offset + 3)
    ))
    faces.extend((
        (offset + 2, offset + 0, offset + 3),
        (offset + 2, offset + 1, offset + 0),
        (offset + 6, offset + 4, offset + 5),
        (offset + 6, offset + 7, offset + 4),
        (offset + 5, offset + 0, offset + 1),
        (offset + 5, offset + 2, offset + 6),
        (offset + 7, offset + 2, offset + 3),
        (offset + 4, offset + 3, offset + 0),
        (offset + 5, offset + 4, offset + 0),
        (offset + 5, offset + 1, offset + 2),
        (offset + 7, offset + 6, offset + 2),
        (offset + 4, offset + 7, offset + 3)
    ))


def gen_cylinder_geom(mat, coords, lines, faces):
    num_segments = const.BONE_SHAPE_CYLINDER_SEGMENTS_COUNT
    offset = len(coords)
    radius = 1.0
    half_height = 0.5

    gen_circle(
        radius,
        num_segments,
        lambda x, y: coords.append(mat @ mathutils.Vector((x, -half_height, y))),
        lines,
        offset=offset
    )
    gen_circle(
        radius,
        num_segments,
        lambda x, y: coords.append(mat @ mathutils.Vector((x, +half_height, y))),
        lines,
        offset=offset+num_segments+1
    )

    bottom_start = 0
    top_start = num_segments + 1

    # bottom and top faces
    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        faces.append((
            bottom_start + offset,
            bottom_start + i + offset,
            bottom_start + next_i + offset
        ))
        faces.append((
            top_start + offset,
            top_start + next_i + offset,
            top_start + i + offset
        ))

    # side faces
    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        faces.append((
            bottom_start + i + offset,
            top_start + i + offset,
            bottom_start + next_i + offset
        ))
        faces.append((
            top_start + i + offset,
            top_start + next_i + offset,
            bottom_start + next_i + offset
        ))

    start_index = len(coords)

    coords.extend([
        mat @ mathutils.Vector((-radius, -half_height, 0)),
        mat @ mathutils.Vector((-radius, +half_height, 0)),
        mat @ mathutils.Vector((+radius, -half_height, 0)),
        mat @ mathutils.Vector((+radius, +half_height, 0)),
        mat @ mathutils.Vector((0, -half_height, -radius)),
        mat @ mathutils.Vector((0, +half_height, -radius)),
        mat @ mathutils.Vector((0, -half_height, +radius)),
        mat @ mathutils.Vector((0, +half_height, +radius))
    ])
    for i in range(start_index, start_index + 8, 2):
        lines.extend((
            (i, i + 1),
            (i + 1, i)
        ))


def gen_sphere_geom(mat, coords, lines, faces):
    offset = len(coords)
    num_segments = const.BONE_SHAPE_SPHERE_SEGMENTS_COUNT

    # generate vertex coordinates
    for i in range(num_segments + 1):
        theta = math.pi * i / num_segments
        for j in range(num_segments):
            phi = 2 * math.pi * j / num_segments
            x = math.sin(theta) * math.cos(phi)
            y = math.sin(theta) * math.sin(phi)
            z = math.cos(theta)
            coords.append(mat @ mathutils.Vector((x, y, z)))

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
                faces.append((
                    current + offset,
                    next_lat + offset,
                    next_lat_lon + offset))
            if i != 0:
                faces.append((
                    current + offset,
                    next_lat_lon + offset,
                    next_lon + offset
                ))

            # generate wire indices
            if i == num_segments // 2:
                lines.append((current + offset, next_lon + offset))
            if j == num_segments // 2 or j == 0:
                lines.append((current + offset, next_lat + offset))
            if j == num_segments // 4 or j == num_segments // 4 * 3:
                lines.append((current + offset, next_lat + offset))


def gen_cross_geom(size, mat, coords, lines):
    offset = len(coords)

    coords.extend((
        mat @ mathutils.Vector((-size, 0.0, 0.0)),
        mat @ mathutils.Vector((+size, 0.0, 0.0)),
        mat @ mathutils.Vector((0.0, -size, 0.0)),
        mat @ mathutils.Vector((0.0, +size, 0.0)),
        mat @ mathutils.Vector((0.0, 0.0, -size)),
        mat @ mathutils.Vector((0.0, 0.0, +size))
    ))

    for i in range(3):
        index = offset + i * 2
        lines.append((index, index + 1))
