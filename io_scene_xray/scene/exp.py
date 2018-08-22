
import io
import string

from .. import xray_io
from . import fmt


def write_objects_count(chunked_writer, bpy_objs):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('I', len(bpy_objs))
    chunked_writer.put(fmt.Chunks.OBJECTS_COUNT_CHUNK, packed_writer)


def write_object_body(chunked_writer, bpy_obj):
    body_chunked_writer = xray_io.ChunkedWriter()

    packed_reader = xray_io.PackedWriter()
    packed_reader.putf('I', 0)
    body_chunked_writer.put(fmt.Chunks.CUSTOMOBJECT_CHUNK_FLAGS, packed_reader)

    if bpy_obj.xray.export_path:
        if bpy_obj.xray.export_path[-1] != '\\':
            bpy_obj.xray.export_path += '\\'
    object_name = bpy_obj.xray.export_path + bpy_obj.name
    if object_name.endswith('.object'):
        object_name = object_name[0 : -len('.object')]

    packed_reader = xray_io.PackedWriter()
    packed_reader.puts(object_name)
    body_chunked_writer.put(fmt.Chunks.CUSTOMOBJECT_CHUNK_NAME, packed_reader)

    packed_reader = xray_io.PackedWriter()
    packed_reader.putf('3f', bpy_obj.location[0], bpy_obj.location[2], bpy_obj.location[1])
    rotation_matrix = bpy_obj.rotation_euler.to_matrix()
    rotation_euler = rotation_matrix.to_euler('YXZ')
    packed_reader.putf(
        '3f',
        rotation_euler.x,
        rotation_euler.z,
        rotation_euler.y
    )
    packed_reader.putf('3f', bpy_obj.scale[0], bpy_obj.scale[2], bpy_obj.scale[1])
    body_chunked_writer.put(fmt.Chunks.CUSTOMOBJECT_CHUNK_TRANSFORM, packed_reader)

    packed_reader = xray_io.PackedWriter()
    packed_reader.putf('H', fmt.SCENEOBJ_CURRENT_VERSION)
    body_chunked_writer.put(fmt.Chunks.SCENEOBJ_CHUNK_VERSION, packed_reader)

    packed_reader = xray_io.PackedWriter()
    if object_name[-4] == '.':
        if object_name[-1] in string.digits and \
           object_name[-2] in string.digits and \
           object_name[-3] in string.digits:
            object_name = object_name[0 : -4]
    packed_reader.puts(object_name)
    body_chunked_writer.put(fmt.Chunks.SCENEOBJ_CHUNK_REFERENCE, packed_reader)

    packed_reader = xray_io.PackedWriter()
    packed_reader.putf('I', 0)
    body_chunked_writer.put(fmt.Chunks.SCENEOBJ_CHUNK_FLAGS, packed_reader)

    chunked_writer.put(fmt.Chunks.CHUNK_OBJECT_BODY, body_chunked_writer)


def write_object_class(chunked_writer):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('I', 2)    # object class
    chunked_writer.put(fmt.Chunks.CHUNK_OBJECT_CLASS, packed_writer)


def write_scene_object(bpy_obj, objects_chunked_writer, object_index):
    chunked_writer = xray_io.ChunkedWriter()
    write_object_class(chunked_writer)
    write_object_body(chunked_writer, bpy_obj)
    objects_chunked_writer.put(object_index, chunked_writer)


def write_scene_objects(chunked_writer, bpy_objs):
    objects_chunked_writer = xray_io.ChunkedWriter()
    export_object_index = 0
    for object_index, bpy_obj in enumerate(bpy_objs):
        if bpy_obj.xray.isroot:
            write_scene_object(bpy_obj, objects_chunked_writer, export_object_index)
            export_object_index += 1
    chunked_writer.put(fmt.Chunks.SCENE_OBJECTS_CHUNK, objects_chunked_writer)


def write_object_tools_version(chunked_writer):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('H', fmt.OBJECT_TOOLS_VERSION)
    chunked_writer.put(fmt.Chunks.SCENE_VERSION_CHUNK, packed_writer)


def write_objects(root_chunked_writer, bpy_objs):
    chunked_writer = xray_io.ChunkedWriter()
    write_object_tools_version(chunked_writer)
    write_scene_objects(chunked_writer, bpy_objs)
    write_objects_count(chunked_writer, bpy_objs)
    root_chunked_writer.put(fmt.Chunks.OBJECTS_CHUNK, chunked_writer)


def write_header(chunked_writer):
    packed_writer = xray_io.PackedWriter()
    packed_writer.putf('I', fmt.FORMAT_VERSION)
    chunked_writer.put(fmt.Chunks.VERSION_CHUNK, packed_writer)


def _export(bpy_objs, chunked_writer):
    write_header(chunked_writer)
    write_objects(chunked_writer, bpy_objs)


def export_file(bpy_objs, filepath):
    with io.open(filepath, 'wb') as file:
        writer = xray_io.ChunkedWriter()
        _export(bpy_objs, writer)
        file.write(writer.data)
