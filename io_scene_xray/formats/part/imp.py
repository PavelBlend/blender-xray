# standart modules
import os

# addon modules
from . import fmt
from .. import obj
from ... import log
from ... import text
from ... import utils
from ... import rw


def read_soc_scene_object(data):
    pos = None
    rot = None
    scl = None
    ref = None

    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == fmt.Chunks.OBJECT_BODY:
            body_reader = rw.read.ChunkedReader(chunk_data)

            for body_chunk_id, body_chunk_data in body_reader:
                if body_chunk_id == fmt.Chunks.REFERENCE:
                    reader = rw.read.PackedReader(body_chunk_data)
                    ver = reader.uint32()
                    length = reader.uint32()
                    ref = reader.gets()

                elif body_chunk_id == fmt.Chunks.TRANSFORM:
                    reader = rw.read.PackedReader(body_chunk_data)
                    pos = reader.getf('<3f')
                    rot = reader.getf('<3f')
                    scl = reader.getf('<3f')

    return ref, pos, rot, scl


def read_soc_scene_objects(data):
    refs = []
    pos = []
    rot = []
    scl = []

    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:
        ref, position, rotation, scale = read_soc_scene_object(chunk_data)

        refs.append(ref)
        pos.append(position)
        rot.append(rotation)
        scl.append(scale)

    return refs, pos, rot, scl


def read_soc_tools_data(data):
    chunked_reader = rw.read.ChunkedReader(data)

    refs = []
    pos = []
    rot = []
    scl = []

    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == fmt.Chunks.OBJECTS:
            refs, pos, rot, scl = read_soc_scene_objects(chunk_data)
            break

    return refs, pos, rot, scl


def read_soc_objects(data):
    chunked_reader = rw.read.ChunkedReader(data)

    refs = []
    pos = []
    rot = []
    scl = []

    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == fmt.Chunks.TOOLS_DATA:
            refs, pos, rot, scl = read_soc_tools_data(chunk_data)
            break

    return refs, pos, rot, scl


def read_cs_cop_objects(ltx):
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

        obj_name = params.get('name', None)
        position = params.get('position', None)
        rotation = params.get('rotation', None)
        scale = params.get('scale', None)

        refs.append(ref)

        if position:
            pos.append(list(map(float, position.split(','))))
        else:
            pos.append(None)

        if rotation:
            rot.append(list(map(float, rotation.split(','))))
        else:
            rot.append(None)

        if scale:
            scl.append(list(map(float, scale.split(','))))
        else:
            scl.append(None)

    return refs, pos, rot, scl


def import_objects(refs, pos, rot, scl, context, level_name):
    if not len(refs):
        raise log.AppError('File has no objects!')

    imported_objects = {}
    context.before_import_file()
    collection = utils.version.create_collection(level_name)

    imported_count = 0

    for index, ref in enumerate(refs):
        object_path = os.path.join(context.objects_folder, ref)

        if object_path[-1] == '\r':
            object_path = object_path[ : -1]

        if not object_path.endswith('.object'):
            object_path += '.object'

        if not os.path.exists(object_path):
            log.warn(
                text.warn.scene_no_file,
                file=object_path
            )
            continue

        loaded_object = imported_objects.get(ref)

        if loaded_object:
            imported_object = loaded_object.copy()
            for child_object in loaded_object.children:
                new_child = child_object.copy()
                new_child.parent = imported_object
        else:
            imported_object = obj.imp.main.import_file(object_path, context)
            imported_objects[ref] = imported_object
            utils.version.unlink_object_from_collections(imported_object)
            exp_dir = os.path.dirname(ref)
            if exp_dir:
                imported_object.xray.export_path = exp_dir

        utils.version.link_object_to_collection(imported_object, collection)

        position = pos[index]
        rotate = rot[index]
        scale = scl[index]

        if position:
            imported_object.location = position[0], position[2], position[1]

        if rotate:
            imported_object.rotation_mode = 'XYZ'
            imported_object.rotation_euler = rotate[0], rotate[2], rotate[1]

        if scale:
            imported_object.scale = scale[0], scale[2], scale[1]

        imported_count += 1

    if not imported_count:
        utils.version.remove_collection(collection)


@log.with_context(name='import-part')
@utils.stats.timer
def import_file(file_path, context):
    utils.stats.status('Import File: "{}"'.format(file_path))

    level_name = os.path.basename(os.path.dirname(file_path))
    file_data = rw.utils.get_file_data(file_path)

    try:
        ltx_data = file_data.decode(encoding='cp1251')
        ltx = rw.ltx.LtxParser()
        ltx.from_str(ltx_data)
    except:
        ltx = None

    if ltx:
        refs, pos, rot, scl = read_cs_cop_objects(ltx)
    else:
        refs, pos, rot, scl = read_soc_objects(file_data)

    import_objects(refs, pos, rot, scl, context, level_name)
