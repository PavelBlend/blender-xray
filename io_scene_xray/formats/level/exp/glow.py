# blender modules
import bpy

# addon modules
from . import shader
from .. import fmt
from .... import text
from .... import log
from .... import rw


def _write_glow(glows_writer, glow_obj, level):
    exported = False

    if glow_obj.type != 'MESH':
        return exported

    glow_mesh = glow_obj.data

    faces_count = len(glow_mesh.polygons)
    if not faces_count:
        raise log.AppError(
            text.error.level_bad_glow,
            log.props(
                object=glow_obj.name,
                faces_count=faces_count
            )
        )

    dim_max = max(glow_obj.dimensions)
    glow_radius = dim_max / 2
    if glow_radius < 0.0005:
        raise log.AppError(
            text.error.level_bad_glow_radius,
            log.props(
                object=glow_obj.name,
                radius=glow_radius
            )
        )

    bpy_mat, shader_index = shader.get_shader_index(
        level,
        glow_obj,
        text.error.level_no_mat_glow,
        text.error.level_glow_many_mats,
        text.error.level_glow_empty_mat
    )

    # position
    glows_writer.putf(
        '<3f',
        glow_obj.location[0],
        glow_obj.location[2],
        glow_obj.location[1]
    )

    # radius
    glows_writer.putf('<f', glow_radius)

    # shader index
    glows_writer.putf('<H', shader_index + 1)    # +1 - skip first empty shader

    exported = True

    return exported


def write_glows(level_writer, level_object, level):
    glows_writer = rw.write.PackedWriter()

    # search glows object
    glows_obj = bpy.data.objects.get(level_object.xray.level.glows_obj)

    if not glows_obj:

        for child_name in level.visuals_cache.children[level_object.name]:
            child_obj = bpy.data.objects[child_name]
            if child_obj.name.startswith('glows'):
                glows_obj = child_obj
                break

    # export glows
    glows_count = 0

    if glows_obj:

        for glow_name in level.visuals_cache.children[glows_obj.name]:
            glow_obj = bpy.data.objects[glow_name]
            exported = _write_glow(glows_writer, glow_obj, level)

            if exported:
                glows_count += 1

    if not glows_count:
        raise log.AppError(
            text.error.level_no_glow,
            log.props(object=level_object.name)
        )

    # write glows chunk
    level_writer.put(fmt.Chunks13.GLOWS, glows_writer)
