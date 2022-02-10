# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import obj
from .. import log
from .. import text
from .. import utils
from .. import ie_utils
from .. import version_utils
from .. import xray_ltx


def import_cs_cop_objects(ltx, context, level_name):
    imported_objects = {}
    collection = version_utils.create_collection(level_name)
    objects_count = 0
    for section_name, section in ltx.sections.items():
        if not section_name.lower().startswith('object_'):
            continue
        params = section.params
        ref = params.get('reference_name', None)
        if ref:
            objects_count += 1
            object_path = os.path.join(context.objects_folder, ref)
            if object_path[-1] == '\r':
                object_path = object_path[ : -1]
            if not object_path.endswith('.object'):
                object_path += '.object'
            if os.path.exists(object_path):
                loaded_object = imported_objects.get(ref)
                if not loaded_object:
                    context.before_import_file()
                    imported_object = obj.imp.import_file(object_path, context)
                    version_utils.unlink_object_from_collections(imported_object)
                    exp_dir = os.path.dirname(ref)
                    if exp_dir:
                        imported_object.xray.export_path = exp_dir + os.sep
                    imported_objects[ref] = imported_object
                else:
                    imported_object = loaded_object.copy()
                    for child_object in loaded_object.children:
                        new_child = child_object.copy()
                        new_child.parent = imported_object
                version_utils.link_object_to_collection(imported_object, collection)
                obj_name = params.get('name', None)
                pos = params.get('position', None)
                rot = params.get('rotation', None)
                scale = params.get('scale', None)
                if obj_name:
                    if obj_name.endswith('\r'):
                        obj_name = obj_name[ : -1]
                    imported_object.name = obj_name
                if pos:
                    pos = list(map(float, pos.split(',')))
                    imported_object.location = pos[0], pos[2], pos[1]
                if rot:
                    imported_object.rotation_mode = 'XYZ'
                    rot = list(map(float, rot.split(',')))
                    imported_object.rotation_euler = rot[0], rot[2], rot[1]
                if scale:
                    scale = list(map(float, scale.split(',')))
                    imported_object.scale = scale[0], scale[2], scale[1]
            else:
                log.warn(
                    text.warn.scene_no_file,
                    file=object_path
                )
    if not objects_count:
        raise utils.AppError('File has no objects!')


def import_soc_objects(data, context, level_name):
    raise utils.AppError('Binary Format not Supported!')


@log.with_context(name='import-part')
def import_file(file_path, context):
    log.update(path=file_path)
    ie_utils.check_file_exists(file_path)
    level_name = os.path.basename(os.path.dirname(file_path))
    file_data = utils.read_file(file_path)
    try:
        ltx_data = file_data.decode(encoding='cp1251')
        ltx = xray_ltx.StalkerLtxParser(file_path, data=ltx_data)
    except:
        ltx = None
    if ltx:
        import_cs_cop_objects(ltx, context, level_name)
    else:
        import_soc_objects(file_data, context, level_name)
