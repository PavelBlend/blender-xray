# standart modules
import os

# addon modules
from . import fmt
from .. import obj
from ... import log
from ... import text
from ... import utils
from ... import rw


def _read_soc_scene_object_body(data):
    pos = None
    rot = None
    scl = None
    ref = None

    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:

        # reference
        if chunk_id == fmt.Chunks.REFERENCE:
            reader = rw.read.PackedReader(chunk_data)
            file_version = reader.uint32()
            length = reader.uint32()
            ref = reader.gets()

        # transforms
        elif chunk_id == fmt.Chunks.TRANSFORM:
            reader = rw.read.PackedReader(chunk_data)
            pos = reader.getf('<3f')
            rot = reader.getf('<3f')
            scl = reader.getf('<3f')

    return ref, pos, rot, scl


def _read_soc_scene_object(data):
    pos = None
    rot = None
    scl = None
    ref = None

    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:

        if chunk_id == fmt.Chunks.OBJECT_BODY:
            ref, pos, rot, scl = _read_soc_scene_object_body(chunk_data)
            break

    return ref, pos, rot, scl


def _read_soc_scene_objects(data):
    refs = []
    pos = []
    rot = []
    scl = []

    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:
        ref, position, rotation, scale = _read_soc_scene_object(chunk_data)

        refs.append(ref)
        pos.append(position)
        rot.append(rotation)
        scl.append(scale)

    return refs, pos, rot, scl


def _read_soc_tools_data(data):
    chunked_reader = rw.read.ChunkedReader(data)

    refs = []
    pos = []
    rot = []
    scl = []

    for chunk_id, chunk_data in chunked_reader:

        if chunk_id == fmt.Chunks.OBJECTS:
            refs, pos, rot, scl = _read_soc_scene_objects(chunk_data)
            break

    return refs, pos, rot, scl


def _read_soc_objects(data):
    chunked_reader = rw.read.ChunkedReader(data)

    refs = []
    pos = []
    rot = []
    scl = []

    for chunk_id, chunk_data in chunked_reader:

        if chunk_id == fmt.Chunks.TOOLS_DATA:
            refs, pos, rot, scl = _read_soc_tools_data(chunk_data)
            break

    return refs, pos, rot, scl


def _read_cs_cop_objects(ltx):
    refs = []
    pos = []
    rot = []
    scl = []

    for section_name, section in ltx.sections.items():
        if not section_name.lower().startswith('object_'):
            continue

        params = section.params
        ref = params.get('reference_name', None)

        if not ref:
            continue

        refs.append(ref)

        obj_name = params.get('name', None)
        position = params.get('position', None)
        rotation = params.get('rotation', None)
        scale = params.get('scale', None)

        for elem, array in zip((position, rotation, scale), (pos, rot, scl)):
            if elem:
                array.append(list(map(float, elem.split(','))))
            else:
                array.append(None)

    return refs, pos, rot, scl


def _import_object(context, object_path, imported_objects, ref):
    bpy_object = obj.imp.main.import_file(object_path, context)
    imported_objects[ref] = bpy_object

    utils.version.unlink_object_from_collections(bpy_object)
    utils.ie.set_export_path(bpy_object, '', ref)

    return bpy_object


def _copy_object(loaded_object):
    bpy_object = loaded_object.copy()

    for child_object in loaded_object.children:
        new_child = child_object.copy()
        new_child.parent = bpy_object

    return bpy_object


def _set_obj_transforms(bpy_object, position, rotate, scale):
    if position:
        bpy_object.location = position[0], position[2], position[1]

    if rotate:
        bpy_object.rotation_mode = 'XYZ'
        bpy_object.rotation_euler = rotate[0], rotate[2], rotate[1]

    if scale:
        bpy_object.scale = scale[0], scale[2], scale[1]


def _is_exists_ref_file(context, ref):
    exists = False

    for obj_folder in context.objects_folders:
        if not obj_folder:
            continue

        object_path = os.path.join(obj_folder, ref)

        if object_path[-1] == '\r':
            object_path = object_path[ : -1]

        if not object_path.endswith('.object'):
            object_path += '.object'

        if os.path.exists(object_path):
            exists = True
            break

    return exists, object_path


def _import_objects(refs, pos, rot, scl, context, level_name):
    if not len(refs):
        raise log.AppError(text.error.part_no_objs)

    imported_count = 0
    imported_objects = {}
    context.before_import_file()
    collection = utils.version.create_collection(level_name)

    for index, ref in enumerate(refs):
        exists, object_path = _is_exists_ref_file(context, ref)

        if not exists:
            log.warn(
                text.warn.scene_no_file,
                file=object_path
            )
            continue

        loaded_object = imported_objects.get(ref)

        if loaded_object:
            ref_object = _copy_object(loaded_object)

        else:
            ref_object = _import_object(
                context,
                object_path,
                imported_objects,
                ref
            )

        utils.version.link_object_to_collection(ref_object, collection)

        position = pos[index]
        rotate = rot[index]
        scale = scl[index]

        _set_obj_transforms(ref_object, position, rotate, scale)

        imported_count += 1

    if not imported_count:
        utils.version.remove_collection(collection)


@log.with_context(name='import-part')
@utils.stats.timer
def import_file(file_path, context):
    utils.stats.status('Import File', file_path)

    level_name = os.path.basename(os.path.dirname(file_path))
    file_data = rw.utils.get_file_data(file_path)

    try:
        ltx_data = file_data.decode(encoding='cp1251')
        ltx = rw.ltx.LtxParser()
        ltx.from_str(ltx_data)
    except:
        ltx = None

    if ltx:
        refs, pos, rot, scl = _read_cs_cop_objects(ltx)
    else:
        refs, pos, rot, scl = _read_soc_objects(file_data)

    _import_objects(refs, pos, rot, scl, context, level_name)
