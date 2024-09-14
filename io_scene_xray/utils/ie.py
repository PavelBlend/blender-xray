# standart modules
import os

# blender modules
import bpy
import mathutils

# addon modules
from . import draw
from . import mesh
from . import version
from .. import log
from .. import text


class BaseOperator(bpy.types.Operator):
    report_catcher = None

    def __getattribute__(self, item):
        if (item == 'report') and (self.report_catcher is not None):
            return self.report_catcher

        return super().__getattribute__(item)


# import/export utils


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
        operator.report(
            {'ERROR'},
            text.get_tip(text.error.no_sel_files)
        )

    return has_sel


def get_tex_dirs(operator=None):
    tex_folder = ''
    tex_mod_folder = ''

    lvl_folder = ''
    lvl_mod_folder = ''

    pref = version.get_preferences()

    # simple mode
    if pref.paths_mode == 'BASE':
        tex_folder = bpy.path.abspath(pref.textures_folder_auto)
        lvl_folder = bpy.path.abspath(pref.levels_folder_auto)

    # advanced mode
    else:
        used_config = pref.paths_configs.get(pref.used_config)

        if used_config:

            # platform
            platform_paths = pref.paths_presets.get(used_config.platform)

            if platform_paths:
                tex_folder = platform_paths.textures_folder_auto
                tex_folder = bpy.path.abspath(tex_folder)

                lvl_folder = platform_paths.levels_folder_auto
                lvl_folder = bpy.path.abspath(lvl_folder)

            # mod
            mod_paths = pref.paths_presets.get(used_config.mod)

            if mod_paths:
                tex_mod_folder = mod_paths.textures_folder_auto
                tex_mod_folder = bpy.path.abspath(tex_mod_folder)

                lvl_mod_folder = mod_paths.levels_folder_auto
                lvl_mod_folder = bpy.path.abspath(lvl_mod_folder)

    if not tex_folder:
        if operator:
            operator.report({'WARNING'}, 'No textures folder specified')

    return tex_folder, tex_mod_folder, lvl_folder, lvl_mod_folder


def get_pref_paths(prop_name):
    platform_folder = ''
    mod_folder = ''

    pref = version.get_preferences()

    if not pref:
        return ('', )

    # simple mode
    if pref.paths_mode == 'BASE':
        val = getattr(pref, prop_name + '_auto')
        platform_folder = bpy.path.abspath(val)

    # advanced mode
    else:
        used_config = pref.paths_configs.get(pref.used_config)

        if used_config:

            # platform
            platform_paths = pref.paths_presets.get(used_config.platform)

            if platform_paths:
                val = getattr(platform_paths, prop_name + '_auto')
                platform_folder = bpy.path.abspath(val)

            # mod
            mod_paths = pref.paths_presets.get(used_config.mod)

            if mod_paths:
                val = getattr(mod_paths, prop_name + '_auto')
                mod_folder = bpy.path.abspath(val)

    return mod_folder, platform_folder


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


def _get_paths_configs():
    pref = version.get_preferences()

    # simple mode
    if pref.paths_mode == 'BASE':
        platform_paths = pref
        mod_paths = None

    # advanced mode
    else:
        platform_paths = None
        mod_paths = None

        used_config = pref.paths_configs.get(pref.used_config)

        if used_config:

            # platform
            platform_paths = pref.paths_presets.get(used_config.platform)

            # mod
            mod_paths = pref.paths_presets.get(used_config.mod)

    return mod_paths, platform_paths


def open_imp_exp_folder(operator, path_prop):
    if not hasattr(operator, 'init'):
        operator.init = True

        space = bpy.context.space_data
        params = space.params

        mod_paths, platform_paths = _get_paths_configs()

        path = None
        for paths_pref in (mod_paths, platform_paths):
            if paths_pref:
                path = getattr(paths_pref, path_prop + '_auto')
                break

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
    return '[{0:.6f}, {1:.6f}, {2:.6f}]'.format(*scale)


def check_armature_scale(scale, bpy_root, bpy_arm_obj):
    values = scale.to_tuple()
    mx = max(values)
    EPS = 1e-6  # some matrix transformation inaccuracy
    if any(v / mx < (1 - EPS) for v in values):
        props = dict(
            armature_object=bpy_arm_obj.name,
            armature_scale=format_scale(bpy_arm_obj.scale),
        )
        if bpy_root != bpy_arm_obj:
            props.update(dict(
                root_object=bpy_root.name,
                root_scale=format_scale(bpy_root.scale),
            ))
        raise log.AppError(
            text.error.arm_non_uniform_scale,
            log.props(**props)
        )

    return mx


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


def execute_require_filepath(func):

    def wrapper(self, context):
        if not self.filepath:
            self.report({'ERROR'}, text.warn.no_file)
            return {'CANCELLED'}
        return func(self, context)

    return wrapper


def invoke_require_armature(func):

    def wrapper(self, context, event):

        arm_obj = None
        active = context.active_object

        # get armature-object by active object
        if active and active.type == 'ARMATURE':
            arm_obj = active

        if not arm_obj:

            # get armature-object by selected objects
            arm_objs = []
            for obj in context.selected_objects:
                if obj.type == 'ARMATURE':
                    arm_objs.append(obj)

            if len(arm_objs) > 1:
                self.report({'ERROR'}, text.get_tip(text.error.many_arm_objs))
                return {'CANCELLED'}

            elif len(arm_objs) == 1:
                arm_obj = arm_objs[0]

        if not arm_obj:

            if not active:
                self.report({'ERROR'}, text.get_tip(text.error.no_active_obj))
                return {'CANCELLED'}

            if active.type != 'ARMATURE':
                self.report({'ERROR'}, text.get_tip(text.error.is_not_arm))
                return {'CANCELLED'}

        return func(self, context, event)

    return wrapper


def get_export_path(bpy_obj):
    exp_path = bpy_obj.xray.export_path

    if exp_path:
        exp_path = exp_path.replace('\\', os.sep)
        exp_path = exp_path.replace('/', os.sep)

        if exp_path[-1] != os.sep:
            exp_path += os.sep

    return exp_path


def set_export_path(bpy_obj, folder, file):
    file = file.lower()
    folder = folder.lower()

    if not file.startswith(folder):
        return

    file_dir = os.path.dirname(file)

    if file_dir and not file_dir.endswith(os.sep):
        file_dir += os.sep

    if folder and not folder.endswith(os.sep):
        folder += os.sep

    offset = len(folder)
    exp_path = file_dir[offset : ]

    if exp_path:
        bpy_obj.xray.export_path = exp_path


def no_active_obj_report(op):
    op.report({'ERROR'}, 'No active object!')


def no_selected_obj_report(op):
    op.report({'ERROR'}, 'No selected objects!')


def run_imp_exp_operator(method):    # pragma: no cover
    def wrapper(self, context, event):
        if self.processed:
            self.processed = False
            return method(self, context, event)

        wm = context.window_manager

        # collect addon keymaps
        keymaps_addon = wm.keyconfigs.addon.keymaps['3D View'].keymap_items
        addon_ops = {op_id for op_id in keymaps_addon.keys()}

        # collect operators keymaps
        keys = {}
        current_op_key = None

        if version.IS_293:
            config = 'Blender user'
        elif version.IS_28:
            config = 'blender user'
        else:
            config = 'Blender User'
        keymaps = wm.keyconfigs[config].keymaps['3D View'].keymap_items

        for op_id in addon_ops:
            keymap = keymaps.get(op_id)

            if not keymap:
                continue

            if version.IS_3:
                oskey = keymap.oskey_ui
            else:
                oskey = keymap.oskey
            key = (
                keymap.type,
                keymap.shift,
                keymap.ctrl,
                keymap.alt,
                oskey
            )
            keys.setdefault(key, []).append(op_id)

            category, funct = op_id.split('.')
            op_class = getattr(getattr(bpy.ops, category), funct).idname()

            if op_class == self.bl_idname:
                current_op_key = key

        # run operator
        if current_op_key:
            op_ids = keys.get(current_op_key)
            op_ids.sort()

            if len(op_ids) == 1:
                return method(self, context, event)

            elif len(op_ids) > 1:
                key_type, shift, ctrl, alt, oskey = current_op_key

                if shift:
                    shift = 'Shift '
                else:
                    shift = ''

                if ctrl:
                    ctrl = 'Ctrl '
                else:
                    ctrl = ''

                if alt:
                    alt = 'Alt '
                else:
                    alt = ''

                if oskey:
                    oskey = 'OS-Key'
                else:
                    oskey = ''

                key_str = shift + ctrl + alt + oskey + key_type.upper()

                header_text = text.get_tip(text.warn.keymap_assign_more_one)
                draw.show_message(
                    '',    # message
                    [],    # elements
                    header_text.capitalize(),
                    'INFO',
                    operators=op_ids,
                    operators_props=None,
                    message_props=key_str
                )
                return {'FINISHED'}

        else:
            return method(self, context, event)

    return wrapper


def get_sdk_ver(default):
    ver = None

    pref = version.get_preferences()

    if pref.paths_mode == 'BASE':
        ver = default

    else:
        used_config = pref.paths_configs.get(pref.used_config)

        if used_config:

            platform_props = pref.paths_presets.get(used_config.platform)
            mod_props = pref.paths_presets.get(used_config.mod)

            if mod_props:
                ver = mod_props.sdk_ver

            if not ver and platform_props:
                ver = platform_props.sdk_ver

    if not ver:
        ver = default

    return ver


def _select_verts(obj, verts):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    version.set_active_object(obj)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

    for vert_index in verts:
        vert = obj.data.vertices[vert_index]
        vert.select = True


def validate_vertex_weights(bpy_obj, arm_obj):
    exportable_bones_names = [
        bpy_bone.name
        for bpy_bone in arm_obj.data.bones
            if bpy_bone.xray.exportable
    ]
    exportable_groups_indices = [
        group.index
        for group in bpy_obj.vertex_groups
            if group.name in exportable_bones_names
    ]

    ungrouped_verts = set()
    ungrouped_verts_count = 0

    nonexp_vert_groups = set()
    nonexp_group_verts_count = 0

    has_zero_weights = False

    for vertex in bpy_obj.data.vertices:

        weights = []

        if len(vertex.groups):
            exportable_groups_count = 0

            for vertex_group in vertex.groups:

                if vertex_group.group in exportable_groups_indices:
                    exportable_groups_count += 1

                if vertex_group.weight:
                    weights.append(vertex_group.weight)

            if exportable_groups_count:
                if not weights:
                    mesh.check_zero_weight_verts(bpy_obj)
            else:
                nonexp_vert_groups.add(vertex.index)
                nonexp_group_verts_count += 1

        else:
            ungrouped_verts.add(vertex.index)
            ungrouped_verts_count += 1

    if ungrouped_verts:
        _select_verts(bpy_obj, ungrouped_verts)
        raise log.AppError(
            text.error.object_ungroupped_verts,
            log.props(
                object=bpy_obj.name,
                vertices_count=ungrouped_verts_count
            )
        )

    if nonexp_vert_groups:
        _select_verts(bpy_obj, nonexp_vert_groups)
        raise log.AppError(
            text.error.object_nonexp_group_verts,
            log.props(
                object=bpy_obj.name,
                vertices_count=nonexp_group_verts_count
            )
        )
