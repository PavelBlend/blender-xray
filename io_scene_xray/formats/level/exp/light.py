# blender modules
import bpy

# addon modules
from .. import fmt
from .... import rw
from .... import log
from .... import text


def write_lights(level_writer, level, level_object):
    lights_writer = rw.write.PackedWriter()
    children = level.visuals_cache.children
    lights_obj = bpy.data.objects.get(level_object.xray.level.lights_obj)
    lights_count = 0

    if not lights_obj:
        for child_obj_name in children[level_object.name]:
            child_obj = bpy.data.objects[child_obj_name]
            if child_obj.name.startswith('light dynamic'):
                lights_obj = child_obj

    if lights_obj:
        for light_obj_name in children[lights_obj.name]:
            light_obj = bpy.data.objects[light_obj_name]
            data = light_obj.xray.level

            if data.object_type != 'LIGHT_DYNAMIC':
                continue

            lights_count += 1

            euler = light_obj.matrix_world.to_euler('YXZ')
            matrix = euler.to_matrix().to_3x3()
            direction = (matrix[0][1], matrix[2][1], matrix[1][1])

            # write
            lights_writer.putf('<2I', data.controller_id, data.light_type)
            lights_writer.putf('<4f', *data.diffuse)
            lights_writer.putf('<4f', *data.specular)
            lights_writer.putf('<4f', *data.ambient)
            lights_writer.putv3f(light_obj.location)
            lights_writer.putf('<3f', *direction)
            lights_writer.putf('<2f', data.range_, data.falloff)
            lights_writer.putf('<f', data.attenuation_0)
            lights_writer.putf('<f', data.attenuation_1)
            lights_writer.putf('<f', data.attenuation_2)
            lights_writer.putf('<2f', data.theta, data.phi)

        level_writer.put(fmt.Chunks13.LIGHT_DYNAMIC, lights_writer)

    if not lights_count:
        raise log.AppError(
            text.error.level_no_lights,
            log.props(object=level_object.name)
        )
