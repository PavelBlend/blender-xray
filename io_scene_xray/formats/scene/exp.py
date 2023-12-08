# standart modules
import string

# addon modules
from .. import le
from ... import rw
from ... import log
from ... import utils


def write_objects_count(chunked_writer, bpy_objs):
    packed_writer = rw.write.PackedWriter()

    obj_count = 0
    for obj in bpy_objs:
        if obj.xray.isroot:
            obj_count += 1

    packed_writer.putf('<I', obj_count)
    chunked_writer.put(le.fmt.CustomObjectsChunks.OBJECT_COUNT, packed_writer)


def write_object_body(chunked_writer, bpy_obj):
    body_chunked_writer = rw.write.ChunkedWriter()

    packed_reader = rw.write.PackedWriter()
    packed_reader.putf('<I', 3)    # flags
    body_chunked_writer.put(le.fmt.ObjectChunks.FLAGS, packed_reader)

    exp_path = utils.ie.get_export_path(bpy_obj)
    object_name = exp_path + bpy_obj.name
    if len(object_name) > 4 and object_name[-4] == '.':
        if object_name[-1] in string.digits and \
           object_name[-2] in string.digits and \
           object_name[-3] in string.digits:
            object_name = object_name[0 : -4]
    if object_name.endswith('.object'):
        object_name = object_name[0 : -len('.object')]

    packed_reader = rw.write.PackedWriter()
    packed_reader.puts(object_name)
    body_chunked_writer.put(le.fmt.ObjectChunks.NAME, packed_reader)

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
    body_chunked_writer.put(le.fmt.ObjectChunks.TRANSFORM, packed_reader)

    packed_reader = rw.write.PackedWriter()
    packed_reader.putf('<H', le.fmt.OBJECT_VER_SOC)
    body_chunked_writer.put(le.fmt.SceneObjectChunks.VERSION, packed_reader)

    packed_reader = rw.write.PackedWriter()
    packed_reader.putf('<I', 0)    # version
    packed_reader.putf('<I', 0)    # reserved
    packed_reader.puts(object_name)
    body_chunked_writer.put(le.fmt.SceneObjectChunks.REFERENCE, packed_reader)

    packed_reader = rw.write.PackedWriter()
    packed_reader.putf('<I', 0)
    body_chunked_writer.put(le.fmt.SceneObjectChunks.FLAGS, packed_reader)

    chunked_writer.put(le.fmt.SceneChunks.LEVEL_TAG, body_chunked_writer)


def write_object_class(chunked_writer):
    packed_writer = rw.write.PackedWriter()
    packed_writer.putf('<I', 2)    # object class
    chunked_writer.put(le.fmt.CustomObjectChunks.CLASS, packed_writer)


def write_scene_object(bpy_obj, objects_chunked_writer, object_index):
    chunked_writer = rw.write.ChunkedWriter()
    write_object_class(chunked_writer)
    write_object_body(chunked_writer, bpy_obj)
    objects_chunked_writer.put(object_index, chunked_writer)


def write_scene_objects(chunked_writer, bpy_objs):
    objects_chunked_writer = rw.write.ChunkedWriter()
    export_object_index = 0
    for object_index, bpy_obj in enumerate(bpy_objs):
        if bpy_obj.xray.isroot:
            write_scene_object(bpy_obj, objects_chunked_writer, export_object_index)
            export_object_index += 1
    chunked_writer.put(le.fmt.CustomObjectsChunks.OBJECTS, objects_chunked_writer)


def write_object_tools_version(chunked_writer):
    packed_writer = rw.write.PackedWriter()
    packed_writer.putf('<H', le.fmt.OBJECT_TOOLS_VERSION)
    chunked_writer.put(le.fmt.ObjectToolsChunks.VERSION, packed_writer)


def write_objects(root_chunked_writer, bpy_objs):
    chunked_writer = rw.write.ChunkedWriter()
    write_object_tools_version(chunked_writer)
    write_scene_objects(chunked_writer, bpy_objs)
    write_objects_count(chunked_writer, bpy_objs)
    root_chunked_writer.put(
        le.fmt.ToolsChunks.DATA + le.fmt.ClassID.OBJECT,
        chunked_writer
    )


def write_header(chunked_writer):
    packed_writer = rw.write.PackedWriter()
    packed_writer.putf('<I', le.fmt.SCENE_VERSION)
    chunked_writer.put(le.fmt.SceneChunks.VERSION, packed_writer)


def _export(bpy_objs, chunked_writer):
    write_header(chunked_writer)
    write_objects(chunked_writer, bpy_objs)


@log.with_context(name='export-scene-selection')
@utils.stats.timer
def export_file(bpy_objs, file_path):
    utils.stats.status('Export File', file_path)

    writer = rw.write.ChunkedWriter()
    _export(bpy_objs, writer)
    rw.utils.save_file(file_path, writer)
