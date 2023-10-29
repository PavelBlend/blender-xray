# blender modules
import bpy
import mathutils

# addon modules
from . import create
from .. import fmt
from .... import rw
from .... import utils


LIGHT_OBJECT_NAME = 'light'
INT_MAX = 2 ** 31 - 1


def _read_light(packed_reader, data):
    light_type = packed_reader.uint32()    # type of light source
    if light_type > INT_MAX:
        light_type = -1
    data.light_type = light_type

    data.diffuse = packed_reader.getf('<4f')
    data.specular = packed_reader.getf('<4f')
    data.ambient = packed_reader.getf('<4f')

    position = packed_reader.getv3f()
    direction = packed_reader.getv3f()

    data.range_ = packed_reader.getf('<f')[0]    # cutoff range
    data.falloff = packed_reader.getf('<f')[0]
    data.attenuation_0 = packed_reader.getf('<f')[0]    # constant attenuation
    data.attenuation_1 = packed_reader.getf('<f')[0]    # linear attenuation
    data.attenuation_2 = packed_reader.getf('<f')[0]    # quadratic attenuation
    data.theta = packed_reader.getf('<f')[0]    # inner angle of spotlight cone
    data.phi = packed_reader.getf('<f')[0]    # outer angle of spotlight cone

    return position, direction


def _set_light_transforms(light_object, position, direction):
    dir_vec = mathutils.Vector(direction)
    euler = dir_vec.to_track_quat('Y', 'Z').to_euler('XYZ')
    light_object.location = position
    light_object.rotation_euler = euler


def _import_light_v9(packed_reader, light_object):
    data = light_object.xray.level

    # controller id
    controller_id = packed_reader.uint32()    # ???
    if controller_id > INT_MAX:
        controller_id = -1
    data.controller_id = controller_id

    position, direction = _read_light(packed_reader, data)

    _set_light_transforms(light_object, position, direction)


def _import_light_v8(packed_reader, light_object):
    data = light_object.xray.level
    position, direction = _read_light(packed_reader, data)

    dw_frame, flags = packed_reader.getf('<2I')
    affect_static = bool(flags & fmt.FLAG_AFFECT_STATIC)
    affect_dynamic = bool(flags & fmt.FLAG_AFFECT_DYNAMIC)
    procedural = bool(flags & fmt.FLAG_PROCEDURAL)

    name = packed_reader.getf('<{}s'.format(fmt.LIGHT_V8_NAME_LEN))

    if data.light_type == fmt.D3D_LIGHT_POINT:
        data.controller_id = 2
    elif data.light_type == fmt.D3D_LIGHT_DIRECTIONAL:
        data.controller_id = 1

    _set_light_transforms(light_object, position, direction)


def _import_light_v5(packed_reader, light_object):
    data = light_object.xray.level
    position, direction = _read_light(packed_reader, data)

    dw_frame, flags = packed_reader.getf('<2I')
    current_time, speed = packed_reader.getf('<2f')
    key_start, key_count = packed_reader.getf('<2H')

    if data.light_type == fmt.D3D_LIGHT_POINT:
        data.controller_id = 2
    elif data.light_type == fmt.D3D_LIGHT_DIRECTIONAL:
        data.controller_id = 1

    _set_light_transforms(light_object, position, direction)


def _create_light_object(light_index, collection, lights_object):
    object_name = '{0}_{1:0>3}'.format(LIGHT_OBJECT_NAME, light_index)

    if utils.version.IS_28:
        bpy_data = bpy.data.lights
    else:
        bpy_data = bpy.data.lamps

    light = bpy_data.new(object_name, 'SPOT')
    light_object = create.create_object(object_name, light)

    light_object.parent = lights_object
    light_object.xray.is_level = True
    light_object.xray.level.object_type = 'LIGHT_DYNAMIC'

    collection.objects.link(light_object)
    if not utils.version.IS_28:
        utils.version.link_object(light_object)

    return light_object


def _create_lights_object(level_object, collection):
    lights_object = create.create_object('lights', None)

    lights_object.parent = level_object
    level_object.xray.level.lights_obj = lights_object.name

    collection.objects.link(lights_object)
    if not utils.version.IS_28:
        utils.version.link_object(lights_object)

    return lights_object


def import_lights(level, level_object, chunks, chunks_ids):
    data = chunks.pop(chunks_ids.LIGHT_DYNAMIC)
    packed_reader = rw.read.PackedReader(data)
    collection = level.collections[create.LEVEL_LIGHTS_COLLECTION_NAME]

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
