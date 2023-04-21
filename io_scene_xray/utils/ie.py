# standart modules
import os

# blender modules
import bpy
import mathutils

# addon modules
from . import draw
from . import version
from .. import ui
from .. import log
from .. import text


def report_background(self, *args, **kwargs):
    pass


class BaseOperator(bpy.types.Operator):
    report_catcher = None

    def __getattribute__(self, item):
        if (item == 'report') and (self.report_catcher is not None):
            return self.report_catcher

        if item == 'report' and bpy.app.background:
            return report_background

        return super().__getattribute__(item)


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
    if bpy.context.active_object:
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


def get_obj_scale_matrix(bpy_root, bpy_obj):
    if bpy_root == bpy_obj:
        matrix = mathutils.Matrix.Identity(4)
        scale = bpy_root.scale
    else:
        loc = bpy_obj.matrix_world.to_translation()
        loc_mat = mathutils.Matrix.Translation(loc)
        rot_mat = bpy_obj.matrix_world.to_quaternion().to_matrix().to_4x4()
        matrix = version.multiply(loc_mat, rot_mat)
        scale = mathutils.Vector((0.0, 0.0, 0.0))
        scale.x = bpy_root.scale.x * bpy_obj.scale.x
        scale.y = bpy_root.scale.y * bpy_obj.scale.y
        scale.z = bpy_root.scale.z * bpy_obj.scale.z
    return matrix, scale


def get_object_transform_matrix(bpy_obj):
    loc_mat = mathutils.Matrix.Translation(bpy_obj.location)

    if bpy_obj.rotation_mode == 'QUATERNION':
        rot_mat = bpy_obj.rotation_quaternion.to_matrix().to_4x4()
    elif bpy_obj.rotation_mode == 'AXIS_ANGLE':
        rot_mat = mathutils.Matrix.Rotation(
            bpy_obj.rotation_axis_angle[0],
            4,
            bpy_obj.rotation_axis_angle[1:]
        )
    else:
        rot_mat = bpy_obj.rotation_euler.to_matrix().to_4x4()

    return loc_mat, rot_mat


def get_object_world_matrix(bpy_obj):
    loc_mat, rot_mat = get_object_transform_matrix(bpy_obj)
    scl = bpy_obj.scale
    if bpy_obj.parent:
        loc_par, rot_par, scl_par = get_object_world_matrix(bpy_obj.parent)
        loc_mat = version.multiply(loc_par, loc_mat)
        rot_mat = version.multiply(rot_par, rot_mat)
        scl = mathutils.Vector()
        scl.x = scl_par.x * bpy_obj.scale.x
        scl.y = scl_par.y * bpy_obj.scale.y
        scl.z = scl_par.z * bpy_obj.scale.z
    return loc_mat, rot_mat, scl


def format_scale(scale):
    return '[{0:.3f}, {1:.3f}, {2:.3f}]'.format(*scale)


def check_armature_scale(scale, bpy_root, bpy_arm_obj):
    if not scale.x == scale.y == scale.z:
        if bpy_root == bpy_arm_obj:
            raise log.AppError(
                text.error.arm_non_uniform_scale,
                log.props(
                    armature_scale=format_scale(bpy_arm_obj.scale),
                    armature_object=bpy_arm_obj.name
                )
            )
        else:
            raise log.AppError(
                text.error.arm_non_uniform_scale,
                log.props(
                    armature_object=bpy_arm_obj.name,
                    armature_scale=format_scale(bpy_arm_obj.scale),
                    root_object=bpy_root.name,
                    root_scale=format_scale(bpy_root.scale)
                )
            )


def get_arm_obj(root_obj, operator):
    arm_objs = []

    for obj in root_obj.children:
        if obj.type == 'ARMATURE':
            arm_objs.append(obj)

    if root_obj.type == 'ARMATURE':
        arm_objs.append(root_obj)

    if len(arm_objs) > 1:
        operator.report({'WARNING'}, 'Many armatures')
        return

    if not len(arm_objs):
        operator.report({'WARNING'}, 'Has no armatures')
        return

    return arm_objs[0]
