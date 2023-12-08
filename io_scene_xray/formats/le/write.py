# standart modules
import time
import string

# addon modules
from . import fmt
from ... import rw
from ... import utils


def write_level_tag(chunked_writer):
    owner = utils.obj.get_current_user()

    packed_writer = rw.write.PackedWriter()

    packed_writer.puts(owner)
    packed_writer.putf('<I', int(time.time()))

    chunked_writer.put(fmt.SceneChunks.LEVEL_TAG, packed_writer)


def write_objects_count(chunked_writer, bpy_objs):
    obj_count = 0
    for obj in bpy_objs:
        if obj.xray.isroot:
            obj_count += 1

    packed_writer = rw.write.PackedWriter()

    packed_writer.putf('<I', obj_count)

    chunked_writer.put(fmt.CustomObjectsChunks.OBJECT_COUNT, packed_writer)


def write_object_tools_ver(chunked_writer):
    packed_writer = rw.write.PackedWriter()

    packed_writer.putf('<H', fmt.OBJECT_TOOLS_VERSION)

    chunked_writer.put(fmt.ObjectToolsChunks.VERSION, packed_writer)


def write_object_tools_append_random(chunked_writer):
    packed_writer = rw.write.PackedWriter()

    packed_writer.putf('<3f', 1.0, 1.0, 1.0)    # min scale
    packed_writer.putf('<3f', 1.0, 1.0, 1.0)    # max scale

    packed_writer.putf('<3f', 0.0, 0.0, 0.0)    # min rotation
    packed_writer.putf('<3f', 0.0, 0.0, 0.0)    # min rotation

    packed_writer.putf('<I', 0)    # objects count

    chunked_writer.put(fmt.ObjectToolsChunks.APPEND_RANDOM, packed_writer)


def write_object_tools_flags(chunked_writer):
    packed_writer = rw.write.PackedWriter()

    packed_writer.putf('<I', 0)

    chunked_writer.put(fmt.ObjectToolsChunks.FLAGS, packed_writer)


def write_object_body(chunked_writer, bpy_obj):
    exp_path = utils.ie.get_export_path(bpy_obj)
    object_name = exp_path + bpy_obj.name

    if len(object_name) > 4 and object_name[-4] == '.':
        if object_name[-1] in string.digits and \
           object_name[-2] in string.digits and \
           object_name[-3] in string.digits:
            object_name = object_name[0 : -4]

    if object_name.endswith('.object'):
        object_name = object_name[0 : -len('.object')]

    body_chunked_writer = rw.write.ChunkedWriter()

    # flags
    packed_reader = rw.write.PackedWriter()
    packed_reader.putf('<I', 2)
    body_chunked_writer.put(fmt.ObjectChunks.FLAGS, packed_reader)

    # name
    packed_reader = rw.write.PackedWriter()
    packed_reader.puts(object_name)
    body_chunked_writer.put(fmt.ObjectChunks.NAME, packed_reader)

    # transform
    packed_reader = rw.write.PackedWriter()
    packed_reader.putf('<3f', bpy_obj.location[0], bpy_obj.location[2], bpy_obj.location[1])
    rotation_matrix = bpy_obj.rotation_euler.to_matrix()
    rotation_euler = rotation_matrix.to_euler('YXZ')
    packed_reader.putf(
        '<3f',
        rotation_euler.x,
        rotation_euler.z,
        rotation_euler.y
    )
    packed_reader.putf('<3f', bpy_obj.scale[0], bpy_obj.scale[2], bpy_obj.scale[1])
    body_chunked_writer.put(fmt.ObjectChunks.TRANSFORM, packed_reader)

    # version
    packed_reader = rw.write.PackedWriter()
    packed_reader.putf('<H', fmt.OBJECT_VER_SOC)
    body_chunked_writer.put(fmt.SceneObjectChunks.VERSION, packed_reader)

    # reference
    packed_reader = rw.write.PackedWriter()
    packed_reader.putf('<I', 0)    # version
    packed_reader.putf('<I', 0)    # reserved
    packed_reader.puts(object_name)
    body_chunked_writer.put(fmt.SceneObjectChunks.REFERENCE, packed_reader)

    # scene object flags
    packed_reader = rw.write.PackedWriter()
    packed_reader.putf('<I', 0)
    body_chunked_writer.put(fmt.SceneObjectChunks.FLAGS, packed_reader)

    # write main chunk
    chunked_writer.put(fmt.SceneChunks.LEVEL_TAG, body_chunked_writer)


def write_object_class(chunked_writer):
    packed_writer = rw.write.PackedWriter()

    packed_writer.putf('<I', fmt.ClassID.OBJECT)

    chunked_writer.put(fmt.CustomObjectChunks.CLASS, packed_writer)


def write_scene_object(bpy_obj, objects_chunked_writer, object_index):
    chunked_writer = rw.write.ChunkedWriter()

    write_object_class(chunked_writer)
    write_object_body(chunked_writer, bpy_obj)

    objects_chunked_writer.put(object_index, chunked_writer)


def write_scene_objects(chunked_writer, bpy_objs):
    objects_writer = rw.write.ChunkedWriter()
    obj_index = 0

    for bpy_obj in bpy_objs:
        if bpy_obj.xray.isroot:
            write_scene_object(bpy_obj, objects_writer, obj_index)
            obj_index += 1

    chunked_writer.put(fmt.CustomObjectsChunks.OBJECTS, objects_writer)


def write_objects(root_chunked_writer, bpy_objs, part=False):
    chunked_writer = rw.write.ChunkedWriter()

    if part:
        write_level_tag(chunked_writer)
        write_objects_count(chunked_writer, bpy_objs)
        write_scene_objects(chunked_writer, bpy_objs)
        write_object_tools_ver(chunked_writer)
        write_object_tools_flags(chunked_writer)
        write_object_tools_append_random(chunked_writer)

    else:
        write_object_tools_ver(chunked_writer)
        write_scene_objects(chunked_writer, bpy_objs)
        write_objects_count(chunked_writer, bpy_objs)

    root_chunked_writer.put(
        fmt.ToolsChunks.DATA + fmt.ClassID.OBJECT,
        chunked_writer
    )
