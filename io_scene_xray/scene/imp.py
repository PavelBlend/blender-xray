# standart modules
import os

# blender modules
import bpy

# addon modules
from . import fmt
from .. import text
from .. import log
from .. import utils
from .. import ie_utils
from .. import xray_io
from .. import obj
from .. import version_utils


class ImportSceneContext(obj.imp.utility.ImportObjectMeshContext):
    def __init__(self):
        super().__init__()


def _read_scene_version(scene_version_chunk):
    if not scene_version_chunk:
        raise utils.AppError(text.error.scene_bad_file)

    packed_reader = xray_io.PackedReader(scene_version_chunk)
    object_tools_version = packed_reader.getf('<H')[0]

    if object_tools_version != fmt.OBJECT_TOOLS_VERSION:
        raise utils.AppError(
            text.error.scene_obj_tool_ver,
            log.props(version=object_tools_version)
        )


def _read_objects_count(objects_count_chunk):
    if not objects_count_chunk:
        raise utils.AppError(text.error.scene_obj_count)

    packed_reader = xray_io.PackedReader(objects_count_chunk)
    objects_count = packed_reader.getf('<I')[0]

    return objects_count


def _read_object_body(data, imported_objects, import_context):
    chunked_reader = xray_io.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:
        packed_reader = xray_io.PackedReader(chunk_data)
        if chunk_id == fmt.Chunks.SCENEOBJ_CHUNK_REFERENCE:
            if scene_obj_version == fmt.SCENEOBJ_VERSION_SOC:
                version = packed_reader.getf('<I')[0]
                reserved = packed_reader.getf('<I')[0]
            object_path = packed_reader.gets()
            object_name = object_path.split(os.sep)[-1]
        elif chunk_id == fmt.Chunks.CUSTOMOBJECT_CHUNK_TRANSFORM:
            position = packed_reader.getf('<3f')
            rotation = packed_reader.getf('<3f')
            scale = packed_reader.getf('<3f')
        elif chunk_id == fmt.Chunks.SCENEOBJ_CHUNK_VERSION:
            scene_obj_version = packed_reader.getf('<H')[0]

    import_path = os.path.join(
        os.path.abspath(version_utils.get_preferences().objects_folder_auto),
        object_path + '.object'
    )
    if not imported_objects.get(object_path):
        if os.path.exists(import_path):
            imported_object = obj.imp.import_file(import_path, import_context)
            imported_object.location = position[0], position[2], position[1]
            imported_object.rotation_euler = rotation[0], rotation[2], rotation[1]
            imported_object.scale = scale[0], scale[2], scale[1]
            imported_object.xray.export_path = os.path.dirname(object_path) + os.sep
            imported_objects[object_path] = imported_object
        else:
            log.warn(
                text.warn.scene_no_file,
                file=object_path + '.object',
                path=import_path
            )
    else:
        imported_object = imported_objects.get(object_path)
        if imported_object.type == 'EMPTY':
            new_empty = bpy.data.objects.new(imported_object.name, None)
            new_empty.xray.flags = imported_object.xray.flags
            new_empty.xray.export_path = imported_object.xray.export_path
            new_empty.xray.revision.owner = imported_object.xray.revision.owner
            new_empty.xray.revision.ctime_str = imported_object.xray.revision.ctime_str
            version_utils.link_object(new_empty)
            for mesh in imported_object.children:
                new_object = bpy.data.objects.new(mesh.name, mesh.data)
                new_object.parent = new_empty
                new_object.xray.isroot = False
                version_utils.link_object(new_object)
            new_empty.location = position[0], position[2], position[1]
            new_empty.rotation_euler = rotation[0], rotation[2], rotation[1]
            new_empty.scale = scale[0], scale[2], scale[1]
        else:
            new_object = bpy.data.objects.new(imported_object.name, imported_object.data)
            new_object.xray.flags = imported_object.xray.flags
            new_object.xray.export_path = imported_object.xray.export_path
            new_object.xray.revision.owner = imported_object.xray.revision.owner
            new_object.xray.revision.ctime_str = imported_object.xray.revision.ctime_str
            version_utils.link_object(new_object)
            new_object.location = position[0], position[2], position[1]
            new_object.rotation_euler = rotation[0], rotation[2], rotation[1]
            new_object.scale = scale[0], scale[2], scale[1]


def _read_scene_object(data, imported_objects, import_context):
    chunked_reader = xray_io.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == fmt.Chunks.CHUNK_OBJECT_BODY:
            _read_object_body(chunk_data, imported_objects, import_context)


def _read_scene_objects(scene_objects_chunk, objects_count, import_context):
    if not scene_objects_chunk:
        raise utils.AppError(text.error.scene_scn_objs)

    chunked_reader = xray_io.ChunkedReader(scene_objects_chunk)
    object_index = 0

    imported_objects = {}
    for chunk_id, chunk_data in chunked_reader:
        object_index += 1
        _read_scene_object(chunk_data, imported_objects, import_context)


def _read_objects(objects_chunk, import_context):
    if not objects_chunk:
        raise utils.AppError(text.error.scene_objs)

    chunked_reader = xray_io.ChunkedReader(objects_chunk)
    scene_version_chunk = None
    objects_count_chunk = None
    scene_objects_chunk = None

    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == fmt.Chunks.SCENE_VERSION_CHUNK:
            scene_version_chunk = chunk_data
        elif chunk_id == fmt.Chunks.OBJECTS_COUNT_CHUNK:
            objects_count_chunk = chunk_data
        elif chunk_id == fmt.Chunks.SCENE_OBJECTS_CHUNK:
            scene_objects_chunk = chunk_data

    _read_scene_version(scene_version_chunk)
    objects_count = _read_objects_count(objects_count_chunk)
    _read_scene_objects(scene_objects_chunk, objects_count, import_context)


def _read_version(version_chunk):
    if not version_chunk:
        raise utils.AppError(text.error.scene_no_ver)

    chunk_size = len(version_chunk)
    if chunk_size != 4:
        raise utils.AppError(
            text.error.scene_ver_size,
            log.props(size=chunk_size)
        )

    packed_reader = xray_io.PackedReader(version_chunk)
    version = packed_reader.getf('<I')[0]
    if version != fmt.FORMAT_VERSION:
        raise utils.AppError(
            text.error.scene_ver,
            log.props(version=version)
        )


def import_(filepath, chunked_reader, import_context):
    version_chunk = None
    objects_chunk = None

    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == fmt.Chunks.VERSION_CHUNK:
            version_chunk = chunk_data
        elif chunk_id == fmt.Chunks.OBJECTS_CHUNK:
            objects_chunk = chunk_data

    _read_version(version_chunk)
    _read_objects(objects_chunk, import_context)


@log.with_context(name='file')
def import_file(filepath, operator):
    log.update(path=filepath)
    ie_utils.check_file_exists(filepath)
    preferences = version_utils.get_preferences()
    textures_folder = preferences.textures_folder_auto
    objects_folder = preferences.objects_folder_auto
    import_context = ImportSceneContext()
    import_context.textures_folder=textures_folder
    import_context.soc_sgroups=operator.fmt_version == 'soc'
    import_context.import_motions=False
    import_context.split_by_materials=operator.mesh_split_by_materials
    import_context.operator=operator
    import_context.objects_folder=objects_folder
    import_context.before_import_file()
    file_data = utils.read_file(filepath)
    chunked_reader = xray_io.ChunkedReader(file_data)
    import_(filepath, chunked_reader, import_context)
