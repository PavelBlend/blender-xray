# standart modules
import os

# blender modules
import bpy

# addon modules
from . import draw
from . import version
from .. import ui
from .. import text
from .. import log


# import/export utils


def get_draw_fun(operator):
    def menu_func(self, context):
        icon = ui.icons.get_stalker_icon()
        self.layout.operator(
            operator.bl_idname,
            text=draw.build_op_label(operator),
            icon_value=icon
        )
    operator.draw_fun = menu_func
    return menu_func


def check_file_exists(file_path):
    if not os.path.exists(file_path):
        raise log.AppError(
            text.error.file_not_found,
            log.props(file_path=file_path)
        )


def _get_selection_state(context):
    active_object = context.active_object
    selected_objects = set()
    for obj in context.selected_objects:
        selected_objects.add(obj)
    return active_object, selected_objects


def _set_selection_state(active_object, selected_objects):
    bpy.ops.object.select_all(action='DESELECT')
    version.set_active_object(active_object)
    for obj in selected_objects:
        version.select_object(obj)


def set_mode(mode):
    if bpy.context.object:
        bpy.ops.object.mode_set(mode=mode)


def set_initial_state(method):
    def wrapper(self, context, *args):
        context.window.cursor_set('WAIT')
        mode = context.mode
        set_mode('OBJECT')
        active_object, selected_objects = _get_selection_state(context)

        result = method(self, context, *args)

        set_mode('OBJECT')
        _set_selection_state(active_object, selected_objects)
        if mode.startswith('EDIT_'):
            mode = 'EDIT'
        set_mode(mode)
        context.window.cursor_set('DEFAULT')
        return result
    return wrapper
