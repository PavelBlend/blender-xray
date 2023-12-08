# standart modules
import os

# addon modules
from .. import obj
from ... import text
from ... import log
from ... import utils


def set_obj_transforms(obj, loc, rot, scl):
    if loc:
        obj.location = loc[0], loc[2], loc[1]

    if rot:
        obj.rotation_euler = rot[0], rot[2], rot[1]

    if scl:
        obj.scale = scl[0], scl[2], scl[1]


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


def _copy_object(imp_obj, collection, all_objects, position, rotation, scale):
    # copy root
    new_root = imp_obj.copy()
    all_objects.append(new_root)
    utils.stats.created_obj()
    utils.version.link_object_to_collection(new_root, collection)

    # copy meshes
    for child_obj in imp_obj.children:
        new_mesh = child_obj.copy()
        utils.stats.created_obj()
        utils.version.link_object_to_collection(new_mesh, collection)
        new_mesh.parent = new_root
        new_mesh.xray.isroot = False

    # set root-object transforms
    set_obj_transforms(new_root, position, rotation, scale)


def _import_object(
        import_context,
        import_path,
        object_path,
        imported_objects,
        all_objects,
        position,
        rotation,
        scale
    ):

    imp_obj = None

    if os.path.exists(import_path):
        # import file
        imp_obj = obj.imp.main.import_file(import_path, import_context)
        all_objects.append(imp_obj)
        utils.version.unlink_object_from_collections(imp_obj)
        utils.ie.set_export_path(imp_obj, '', object_path)
        imported_objects[object_path] = imp_obj

        # set transforms
        set_obj_transforms(imp_obj, position, rotation, scale)

    else:
        log.warn(
            text.warn.scene_no_file,
            file=object_path + '.object',
            path=import_path
        )

    return imp_obj


def import_objects(name, imp_ctx, references, positions, rotations, scales):

    if not len(references):
        raise log.AppError(text.error.part_no_objs)

    collection = utils.version.create_collection(name)

    imported_count = 0
    refs_count = 0
    imported_objects = {}
    all_objects = []

    for ref, pos, rot, scl in zip(references, positions, rotations, scales):

        if ref is None:
            continue

        refs_count += 1

        # get file path
        import_path = _get_file_path(ref)

        # get imported object
        imp_obj = imported_objects.get(ref)

        if imp_obj:
            # copy object
            _copy_object(imp_obj, collection, all_objects, pos, rot, scl)

        else:
            # import object
            imp_obj = _import_object(
                imp_ctx,
                import_path,
                ref,
                imported_objects,
                all_objects,
                pos,
                rot,
                scl
            )

            if imp_obj:
                utils.version.link_object_to_collection(imp_obj, collection)

        imported_count += 1

    if not imported_count:
        utils.version.remove_collection(collection)

    if not refs_count:
        raise log.AppError(text.error.part_no_objs)

    return all_objects, collection
