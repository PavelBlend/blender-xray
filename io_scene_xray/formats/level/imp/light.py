# blender modules
import bpy
import mathutils

# addon modules
from . import name
from .. import fmt
from .... import rw
from .... import utils


def _read_light(reader, data):
    # type of light source
    data.light_type_name = str(reader.uint32())

    data.diffuse = reader.getf('<4f')
    data.specular = reader.getf('<4f')
    data.ambient = reader.getf('<4f')

    position = reader.getv3f()
    direction = reader.getv3f()

    data.range_ = reader.getf('<f')[0]    # cutoff range
    data.falloff = reader.getf('<f')[0]
    data.attenuation_0 = reader.getf('<f')[0]    # constant attenuation
    data.attenuation_1 = reader.getf('<f')[0]    # linear attenuation
    data.attenuation_2 = reader.getf('<f')[0]    # quadratic attenuation
    data.theta = reader.getf('<f')[0]    # inner angle of spotlight cone
    data.phi = reader.getf('<f')[0]    # outer angle of spotlight cone

    return position, direction


def _set_light_transforms(light_object, position, direction):
    dir_vec = mathutils.Vector(direction)
    euler = dir_vec.to_track_quat('Y', 'Z').to_euler('XYZ')
    light_object.location = position
    light_object.rotation_euler = euler


def _import_light_v9(reader, light_object):
    data = light_object.xray.level

    # controller id
    data.controller_name = str(reader.uint32())

    position, direction = _read_light(reader, data)

    _set_light_transforms(light_object, position, direction)


def _import_light_v8(reader, light_object):
    data = light_object.xray.level
    position, direction = _read_light(reader, data)

    dw_frame, flags = reader.getf('<2I')
    affect_static = bool(flags & fmt.FLAG_AFFECT_STATIC)
    affect_dynamic = bool(flags & fmt.FLAG_AFFECT_DYNAMIC)
    procedural = bool(flags & fmt.FLAG_PROCEDURAL)

    light_name = reader.getf('<{}s'.format(fmt.LIGHT_V8_NAME_LEN))

    if data.light_type == fmt.D3D_LIGHT_POINT:
        data.controller_name = str(fmt.CONTROLLER_STATIC)
    elif data.light_type == fmt.D3D_LIGHT_DIRECTIONAL:
        data.controller_name = str(fmt.CONTROLLER_SUN)

    _set_light_transforms(light_object, position, direction)


def _import_light_v5(reader, light_object):
    data = light_object.xray.level
    position, direction = _read_light(reader, data)

    dw_frame, flags = reader.getf('<2I')
    current_time, speed = reader.getf('<2f')
    key_start, key_count = reader.getf('<2H')

    if data.light_type == fmt.D3D_LIGHT_POINT:
        data.controller_name = str(fmt.CONTROLLER_STATIC)
    elif data.light_type == fmt.D3D_LIGHT_DIRECTIONAL:
        data.controller_name = str(fmt.CONTROLLER_SUN)

    _set_light_transforms(light_object, position, direction)


def _create_light_object(light_index, collection, lights_object):
    object_name = '{0}_{1:0>3}'.format(name.LIGHT_NAME, light_index)

    if utils.version.IS_28:
        bpy_data = bpy.data.lights
    else:
        bpy_data = bpy.data.lamps

    light = bpy_data.new(object_name, 'SPOT')
    light_object = utils.obj.create_object(object_name, light, False)

    light_object.parent = lights_object
    light_object.xray.is_level = True
    light_object.xray.level.object_type = 'LIGHT_DYNAMIC'

    collection.objects.link(light_object)
    if not utils.version.IS_28:
        utils.version.link_object(light_object)

    return light_object


def _create_lights_object(level_object, collection):
    lights_obj = utils.obj.create_object(name.LIGHT_NAME + 's', None, False)

    lights_obj.parent = level_object
    level_object.xray.level.lights_obj = lights_obj.name

    collection.objects.link(lights_obj)
    if not utils.version.IS_28:
        utils.version.link_object(lights_obj)

    return lights_obj


def import_lights(level, level_object, chunks, chunks_ids):
    data = chunks.pop(chunks_ids.LIGHT_DYNAMIC)
    packed_reader = rw.read.PackedReader(data)
    collection = level.collections[name.LEVEL_LIGHTS_COLLECTION_NAME]

    # create lights root-object
    lights_obj = _create_lights_object(level_object, collection)

    # search import function and light size
    if level.xrlc_version >= fmt.VERSION_9:
        light_size = fmt.LIGHT_DYNAMIC_SIZE_V9
        import_light_funct = _import_light_v9

    elif level.xrlc_version == fmt.VERSION_8:
        light_size = fmt.LIGHT_DYNAMIC_SIZE_V8
        import_light_funct = _import_light_v8

    else:
        light_size = fmt.LIGHT_DYNAMIC_SIZE_V5
        import_light_funct = _import_light_v5

    # import light objects
    light_count = len(data) // light_size

    for index in range(light_count):
        light_obj = _create_light_object(index, collection, lights_obj)
        import_light_funct(packed_reader, light_obj)
