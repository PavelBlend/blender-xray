# standart modules
import os

# addon modules
from . import fmt
from .. import obj
from ... import text
from ... import log
from ... import utils
from ... import rw


URL_FOR_ERR = 'https://github.com/PavelBlend/blender-xray/wiki/Scene-Selection-Import'


def _set_obj_transforms(obj, loc, rot, scl):
    obj.location = loc[0], loc[2], loc[1]
    obj.rotation_euler = rot[0], rot[2], rot[1]
    obj.scale = scl[0], scl[2], scl[1]


def _read_object_body_version(chunked_reader):
    # get scene object version
    ver_chunk = chunked_reader.get_chunk(fmt.SceneObjectChunks.VERSION)
    packed_reader = rw.read.PackedReader(ver_chunk)
    ver = packed_reader.getf('<H')[0]

    # check version
    if not ver in (fmt.OBJECT_VER_SOC, fmt.OBJECT_VER_COP):
        raise log.AppError(
            text.error.scene_obj_ver,
            log.props(version=ver)
        )

    return ver


def _read_object_body_data(chunked_reader, ver):
    object_path = None
    position = None
    rotation = None
    scale = None

    for chunk_id, chunk_data in chunked_reader:

        # reference
        if chunk_id == fmt.SceneObjectChunks.REFERENCE:
            packed_reader = rw.read.PackedReader(chunk_data)

            if ver == fmt.OBJECT_VER_SOC:
                version = packed_reader.uint32()
                reserved = packed_reader.uint32()

            object_path = packed_reader.gets()

        # transforms
        elif chunk_id == fmt.ObjectChunks.TRANSFORM:
            packed_reader = rw.read.PackedReader(chunk_data)

            position = packed_reader.getf('<3f')
            rotation = packed_reader.getf('<3f')
            scale = packed_reader.getf('<3f')

    return object_path, position, rotation, scale


def _get_file_path(object_path):
    import_path = None
    objs_folders = utils.ie.get_pref_paths('objects_folder')

    for objs_folder in objs_folders:
        if not objs_folder:
            continue

        import_path = os.path.join(
            os.path.abspath(objs_folder),
            object_path + '.object'
        )
        if os.path.exists(import_path):
            break

    return import_path


def _copy_object(imp_obj, position, rotation, scale):
    # copy root
    new_root = imp_obj.copy()
    utils.stats.created_obj()
    utils.version.link_object(new_root)

    # copy meshes
    for child_obj in imp_obj.children:
        new_mesh = child_obj.copy()
        utils.stats.created_obj()
        utils.version.link_object(new_mesh)
        new_mesh.parent = new_root
        new_mesh.xray.isroot = False

    # set root-object transforms
    _set_obj_transforms(new_root, position, rotation, scale)


def _import_object(
        import_context,
        import_path,
        object_path,
        imported_objects,
        position,
        rotation,
        scale
    ):

    if os.path.exists(import_path):
        # import file
        imp_obj = obj.imp.main.import_file(import_path, import_context)
        utils.ie.set_export_path(imp_obj, '', object_path)
        imported_objects[object_path] = imp_obj

        # set transforms
        _set_obj_transforms(imp_obj, position, rotation, scale)

    else:
        log.warn(
            text.warn.scene_no_file,
            file=object_path + '.object',
            path=import_path
        )


def _read_object_body(data, imported_objects, import_context):
    chunked_reader = rw.read.ChunkedReader(data)

    # read version
    ver = _read_object_body_version(chunked_reader)

    # read object data
    object_path, position, rotation, scale = _read_object_body_data(
        chunked_reader,
        ver
    )

    # get file path
    import_path = _get_file_path(object_path)

    # get imported object
    imp_obj = imported_objects.get(object_path)

    if imp_obj:
        # copy object
        _copy_object(imp_obj, position, rotation, scale)

    else:
        # import object
        _import_object(
            import_context,
            import_path,
            object_path,
            imported_objects,
            position,
            rotation,
            scale
        )


def _read_object(data, imported_objects, import_context):
    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:

        if chunk_id == fmt.SceneChunks.LEVEL_TAG:
            _read_object_body(chunk_data, imported_objects, import_context)
            break


def _read_objects(data, import_context):
    imported_objects = {}
    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:
        _read_object(chunk_data, imported_objects, import_context)


def _read_data(data, import_context):
    chunked_reader = rw.read.ChunkedReader(data)
    objs_chunk = chunked_reader.get_chunk(fmt.CustomObjectsChunks.OBJECTS)
    _read_objects(objs_chunk, import_context)


def _read_version(version_chunk):
    packed_reader = rw.read.PackedReader(version_chunk)
    version = packed_reader.uint32()

    if version != fmt.SCENE_VERSION:
        raise log.AppError(
            text.error.scene_ver,
            log.props(version=version)
        )


def import_(filepath, chunked_reader, import_context):
    # get chunks
    data_chunk_id = fmt.ToolsChunks.DATA + fmt.ClassID.OBJECT
    version_chunk = chunked_reader.get_chunk(fmt.SceneChunks.VERSION)
    data_chunk = chunked_reader.get_chunk(data_chunk_id)

    if not version_chunk or not data_chunk:
        utils.draw.show_message(
            text.error.scene_incorrect_file,
            (text.get_text(text.error.scene_err_info), ),
            text.get_text(text.warn.info_title),
            'ERROR',
            operators=('wm.url_open', ),
            operators_props=({'url': URL_FOR_ERR, }, ),
            operators_labels=(URL_FOR_ERR, )
        )
        return

    # read
    _read_version(version_chunk)
    _read_data(data_chunk, import_context)


@log.with_context(name='import-scene-selection')
@utils.stats.timer
def import_file(file_path, import_context):
    utils.stats.status('Import File', file_path)

    chunked_reader = rw.utils.get_file_reader(file_path, chunked=True)
    import_(file_path, chunked_reader, import_context)
