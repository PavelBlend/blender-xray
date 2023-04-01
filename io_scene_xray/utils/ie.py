# standart modules
import os

# blender modules
import bpy

# addon modules
from . import draw
from . import version
from .. import ui
from .. import log
from .. import text


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
        if mode != 'OBJECT':
            set_mode('OBJECT')
        active_object, selected_objects = _get_selection_state(context)

        result = method(self, context, *args)

        set_mode('OBJECT')
        _set_selection_state(active_object, selected_objects)
        if mode.startswith('EDIT_'):
            mode = 'EDIT'
        if mode not in ('OBJECT', 'EDIT', 'POSE'):
            mode = 'OBJECT'
        set_mode(mode)
        context.window.cursor_set('DEFAULT')
        return result
    return wrapper


def has_selected_files(operator):
    has_sel = True

    if not operator.files:
        has_sel = False

    if len(operator.files) == 1 and not operator.files[0].name:
        has_sel = False

    if not has_sel:
        operator.report({'ERROR'}, 'No files selected!')

    return has_sel


def get_textures_folder(operator):
    pref = version.get_preferences()
    tex_folder = pref.textures_folder_auto
    if not tex_folder:
        operator.report({'WARNING'}, 'No textures folder specified')
    return tex_folder


def import_files(directory, files, imp_fun, context, results=[]):
    for file in files:
        file_path = os.path.join(directory, file.name)

        try:
            result = imp_fun(file_path, context)
            results.append(result)

        except log.AppError as err:
            context.errors.append(err)

        except BaseException as err:
            context.fatal_errors.append((err, file_path))

    report_errors(context)


def report_errors(context):
    for err in context.errors:
        log.err(err)

    for err, file_path in context.fatal_errors:
        log.warn(
            text.error.fatal_import_error,
            file_path=file_path
        )

    if context.fatal_errors:
        first_error = context.fatal_errors[0][0]
        raise first_error


def open_imp_exp_folder(operator, path_prop):
    if not hasattr(operator, 'init'):
        operator.init = True

        space = bpy.context.space_data
        params = space.params

        pref = version.get_preferences()
        path = getattr(pref, path_prop + '_auto')

        if path:
            if isinstance(params.directory, bytes):
                path = bytes(path, encoding='utf-8')

            if not params.directory.startswith(path):
                params.directory = path


EXT_LIST = (
    '.object',
    '.ogf',
    '.dm',
    '.bones',
    '.details',
    '.anm',
    '.skl',
    '.skls',
    '.omf'
)


def add_file_ext(path, ext):
    # remove preview extension
    base, prev_ext = os.path.splitext(path)
    if prev_ext.lower() in EXT_LIST:
        path = base

    # add extension
    if not path.lower().endswith(ext):
        path += ext

    return path
