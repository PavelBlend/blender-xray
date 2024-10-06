# blender modules
import bpy

# addon modules
from .. import text
from .. import utils


MODE_ITEMS = (
    ('ACTIVE_OBJECT', 'Active Object', ''),
    ('SELECTED_OBJECTS', 'Selected Objects', ''),
    ('ALL_OBJECTS', 'All Objects', '')
)


def get_objs_by_mode(operator):
    objects = []

    # active object
    if operator.mode == 'ACTIVE_OBJECT':
        active_obj = bpy.context.active_object
        if active_obj:
            objects.append(active_obj)
        else:
            operator.report({'WARNING'}, text.error.no_active_obj)

    # selected objects
    elif operator.mode == 'SELECTED_OBJECTS':
        if bpy.context.selected_objects:
            objects = [obj for obj in bpy.context.selected_objects]
        else:
            operator.report({'WARNING'}, text.error.no_selected_obj)

    # all objects
    elif operator.mode == 'ALL_OBJECTS':
        if bpy.data.objects:
            objects = [obj for obj in bpy.context.scene.objects]
        else:
            operator.report({'WARNING'}, text.error.no_blend_obj)

    return objects


def select_objs(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for obj_name in objs:
        obj = bpy.data.objects[obj_name]
        utils.version.select_object(obj)
    utils.version.set_active_object(None)


def deselect_objs():
    bpy.ops.object.select_all(action='DESELECT')
    utils.version.set_active_object(None)
