# standart modules
import os

# addon modules
from .. import obj
from ... import text
from ... import log
from ... import utils


def _set_obj_transforms(obj, loc, rot, scl):
    if loc:
        obj.location = loc[0], loc[2], loc[1]

    if rot:
        obj.rotation_euler = rot[0], rot[2], rot[1]

    if scl:
        obj.scale = scl[0], scl[2], scl[1]


def get_file_path(object_path):
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


def copy_object(imp_obj, position, rotation, scale):
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


def import_object(
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
