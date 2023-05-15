# blender modules
import bpy

# addon modules
from .. import fmt
from .... import rw


def write_lights(level_writer, level, level_object):
    light_writer = rw.write.PackedWriter()
    for child_obj_name in level.visuals_cache.children[level_object.name]:
        child_obj = bpy.data.objects[child_obj_name]
        if child_obj.name.startswith('light dynamic'):
            for light_obj_name in level.visuals_cache.children[child_obj.name]:
                light_obj = bpy.data.objects[light_obj_name]
                data = light_obj.xray.level
                controller_id = data.controller_id
                if controller_id == -1:
                    controller_id = 2 ** 32
                light_writer.putf('<I', controller_id)
                light_writer.putf('<I', data.light_type)
                light_writer.putf('<4f', *data.diffuse)
                light_writer.putf('<4f', *data.specular)
                light_writer.putf('<4f', *data.ambient)
                light_writer.putf(
                    '<3f',
                    light_obj.location[0],
                    light_obj.location[2],
                    light_obj.location[1]
                )
                euler = light_obj.matrix_world.to_euler('YXZ')
                matrix = euler.to_matrix().to_3x3()
                direction = (matrix[0][1], matrix[2][1], matrix[1][1])
                light_writer.putf('<3f', direction[0], direction[1], direction[2])
                light_writer.putf('<f', data.range_)
                light_writer.putf('<f', data.falloff)
                light_writer.putf('<f', data.attenuation_0)
                light_writer.putf('<f', data.attenuation_1)
                light_writer.putf('<f', data.attenuation_2)
                light_writer.putf('<f', data.theta)
                light_writer.putf('<f', data.phi)
    level_writer.put(fmt.Chunks13.LIGHT_DYNAMIC, light_writer)
