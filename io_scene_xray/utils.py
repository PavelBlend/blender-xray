# standart modules
import os
import math
import time
import platform
import getpass
import contextlib

# blender modules
import bpy
import bpy_extras
import mathutils
import bmesh

# addon modules
from . import bl_info
from . import log
from . import text
from . import version_utils
from . import xray_io


def is_exportable_bone(bpy_bone):
    return bpy_bone.xray.exportable


def find_bone_exportable_parent(bpy_bone):
    result = bpy_bone.parent
    while (result is not None) and not is_exportable_bone(result):
        result = result.parent
    return result


def version_to_number(major, minor, release):
    return ((major & 0xff) << 24) | ((minor & 0xff) << 16) | (release & 0xffff)


__PLUGIN_VERSION_NUMBER__ = [None]
def plugin_version_number():
    number = __PLUGIN_VERSION_NUMBER__[0]
    if number is None:
        number = version_to_number(*bl_info['version'])
        __PLUGIN_VERSION_NUMBER__[0] = number
    return number


class AppError(Exception):
    def __init__(self, message, ctx=None):
        if ctx is None:
            ctx = log.props()
        super().__init__(message)
        self.ctx = ctx


@contextlib.contextmanager
def logger(name, report):
    lgr = Logger(report)
    try:
        with log.using_logger(lgr):
            yield
    except AppError as err:
        lgr.err(str(err), err.ctx)
        raise err
    finally:
        lgr.flush(name)


class Logger:
    def __init__(self, report):
        self._report = report
        self._full = list()

    def message_format(self, message):
        message = str(message)
        message = text.get_text(message)
        message = message.strip()
        message = message[0].upper() + message[1:]
        return message

    def warn(self, message, ctx=None):
        message = self.message_format(message)
        self._full.append((message, ctx, 'WARNING'))

    def err(self, message, ctx=None):
        message = self.message_format(message)
        self._full.append((message, ctx, 'ERROR'))

    def flush(self, logname='log'):
        uniq = dict()
        message_contexts = {}
        for msg, ctx, typ in self._full:
            uniq[msg] = uniq.get(msg, (0, typ))[0] + 1, typ
            message_contexts.setdefault(msg, []).append(ctx.data)
        if not uniq:
            return

        lines = ['Digest:']
        for msg, (cnt, typ) in uniq.items():
            line = msg
            if cnt > 1:
                line = ('[%dx] ' % cnt) + line
                lines.append(' ' + line)
            else:
                context = message_contexts[msg]
                if context[0]:
                    prop = tuple(context[0].values())[0]
                    if line.endswith('.'):
                        line = line[ : -1]
                    lines.append(' ' + line)
                    line = '{0}: "{1}"'.format(line, prop)
                else:
                    lines.append(' ' + line)
            self._report({typ}, line)

        lines.extend(['', 'Full log:'])
        processed_groups = dict()
        last_line_is_message = False

        def fmt_data(data):
            if log.CTX_NAME in data:
                name = None
                args = []
                for key, val in data.items():
                    if key is log.CTX_NAME:
                        name = val
                    else:
                        args.append('%s=%s' % (key, repr(val)))
                return '%s(%s)' % (name, ', '.join(args))
            return str(data)

        def ensure_group_processed(group):
            nonlocal last_line_is_message
            prefix = processed_groups.get(group, None)
            if prefix is None:
                if group is not None:
                    if group.parent:
                        ensure_group_processed(group.parent)
                    prefix = '| ' * group.depth
                    if last_line_is_message:
                        lines.append(prefix + '|')
                    lines.append('%s+-%s' % (prefix, fmt_data(group.data)))
                    last_line_is_message = False
                    prefix += '|  '
                else:
                    prefix = ''
                processed_groups[group] = prefix
            return prefix


        last_message = None
        last_message_count = 0
        for msg, ctx, typ in self._full:
            data = dict()
            group = ctx
            while group and group.lightweight:
                data.update(group.data)
                group = group.parent
            prefix = ensure_group_processed(group)
            if data:
                if msg.endswith('.'):
                    msg = msg[ : -1]
                msg += (': %s' % data)
            if last_line_is_message and (last_message == msg):
                last_message_count += 1
                lines[-1] = '%s[%dx] %s' % (prefix, last_message_count, msg)
            else:
                lines.append(prefix + msg)
                last_message = msg
                last_message_count = 1
                last_line_is_message = True

        text_data = bpy.data.texts.new(logname)
        text_data.user_clear()
        text_data.from_string('\n'.join(lines))
        self._report(
            {'WARNING'},
            text.warn.full_log.format(text_data.name)
        )


def fix_ensure_lookup_table(bmv):
    if hasattr(bmv, 'ensure_lookup_table'):
        bmv.ensure_lookup_table()


def convert_object_to_space_bmesh(bpy_obj, space_matrix, local=False, split_normals=False, mods=None):
    mesh = bmesh.new()
    temp_obj = None
    if split_normals and version_utils.IS_279:
        temp_mesh = bpy_obj.data.copy()
        temp_obj = bpy_obj.copy()
        temp_obj.data = temp_mesh
        # set sharp edges by face smoothing
        for polygon in temp_mesh.polygons:
            if polygon.use_smooth:
                continue
            for loop_index in polygon.loop_indices:
                loop = temp_mesh.loops[loop_index]
                edge = temp_mesh.edges[loop.edge_index]
                edge.use_edge_sharp = True
        version_utils.link_object(temp_obj)
        version_utils.set_active_object(temp_obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.set_normals_from_faces()
        bpy.ops.object.mode_set(mode='OBJECT')
        exportable_obj = temp_obj
    else:
        exportable_obj = bpy_obj
    # apply shape keys
    if exportable_obj.data.shape_keys:
        if not temp_obj:
            temp_mesh = exportable_obj.data.copy()
            temp_obj = exportable_obj.copy()
            temp_obj.data = temp_mesh
            version_utils.link_object(temp_obj)
            version_utils.set_active_object(temp_obj)
            exportable_obj = temp_obj
        temp_obj.shape_key_add(name='last_shape_key', from_mix=True)
        for shape_key in temp_mesh.shape_keys.key_blocks:
            temp_obj.shape_key_remove(shape_key)
    # apply modifiers
    if mods:
        if not temp_obj:
            temp_mesh = bpy_obj.data.copy()
            temp_obj = bpy_obj.copy()
            temp_obj.data = temp_mesh
            version_utils.link_object(temp_obj)
            version_utils.set_active_object(temp_obj)
            exportable_obj = temp_obj
        override = bpy.context.copy()
        override['active_object'] = temp_obj
        override['object'] = temp_obj
        for mod in mods:
            bpy.ops.object.modifier_apply(override, modifier=mod.name)
    mesh.from_mesh(exportable_obj.data)
    if local:
        mat = mathutils.Matrix()
    else:
        mat = bpy_obj.matrix_world
    mat = version_utils.multiply(space_matrix.inverted(), mat)
    mesh.transform(mat)
    need_flip = False
    for scale_component in mat.to_scale():
        if scale_component < 0:
            need_flip = not need_flip
    if need_flip:
        bmesh.ops.reverse_faces(mesh, faces=mesh.faces)  # flip normals
    fix_ensure_lookup_table(mesh.verts)
    if temp_obj:
        bpy.data.objects.remove(temp_obj)
        bpy.data.meshes.remove(temp_mesh)
    return mesh


def calculate_mesh_bbox(verts, mat=mathutils.Matrix()):
    def vfunc(dst, src, func):
        dst.x = func(dst.x, src.x)
        dst.y = func(dst.y, src.y)
        dst.z = func(dst.z, src.z)

    multiply = version_utils.get_multiply()
    fix_ensure_lookup_table(verts)
    _min = multiply(mat, verts[0].co).copy()
    _max = _min.copy()

    vs = []
    for vertex in verts:
        vfunc(_min, multiply(mat, vertex.co), min)
        vfunc(_max, multiply(mat, vertex.co), max)
        vs.append(_max)

    return _min, _max


def make_relative_texture_path(a_tx_fpath, a_tx_folder):
    a_tx_fpath = a_tx_fpath[len(a_tx_folder):].replace(os.path.sep, '\\')
    if a_tx_fpath.startswith('\\'):
        a_tx_fpath = a_tx_fpath[1:]
    return a_tx_fpath


def gen_texture_name(image, tx_folder, level_folder=None, errors=set()):
    file_path = image.filepath
    a_tx_fpath = os.path.normpath(bpy.path.abspath(file_path))
    a_tx_folder = os.path.abspath(tx_folder)
    a_tx_fpath = os.path.splitext(a_tx_fpath)[0]
    if not level_folder:    # find texture in gamedata\textures folder
        if not a_tx_fpath.startswith(a_tx_folder):
            drive, path_part_1 = os.path.splitdrive(a_tx_fpath)
            file_full_name = os.path.basename(path_part_1)
            file_name, ext = os.path.splitext(file_full_name)
            if path_part_1.count(os.sep) > 1:
                dir_path = os.path.dirname(path_part_1)
                dir_name = os.path.basename(dir_path)
                if file_name.startswith(dir_name + '_'):
                    relative_path = os.path.join(dir_name, file_name)
                    a_tx_fpath = relative_path.replace(os.path.sep, '\\')
                else:
                    a_tx_fpath = file_name
            else:
                a_tx_fpath = file_name
            log.warn(
                text.warn.img_bad_image_path,
                image=image.name,
                image_path=image.filepath,
                textures_folder=a_tx_folder,
                saved_as=a_tx_fpath
            )
        else:
            a_tx_fpath = make_relative_texture_path(a_tx_fpath, a_tx_folder)
    else:
        if a_tx_fpath.startswith(a_tx_folder):    # gamedata\textures folder
            a_tx_fpath = make_relative_texture_path(a_tx_fpath, a_tx_folder)
        elif a_tx_fpath.startswith(level_folder):    # gamedata\levels\level_name folder
            a_tx_fpath = make_relative_texture_path(a_tx_fpath, level_folder)
        else:    # gamedata\levels\level_name\texture_name
            if not file_path in errors:
                log.warn(
                    text.warn.invalid_image_path,
                    image=image.name,
                    path=file_path
                )
                errors.add(file_path)
            a_tx_fpath = os.path.split(a_tx_fpath)[-1]
    return a_tx_fpath


def create_cached_file_data(ffname, fparser):
    class State:
        def __init__(self):
            self._cdata = None
            self._cpath = None

        def get_values(self):
            file_path = ffname()
            if self._cpath == file_path:
                return self._cdata
            tmp = None
            if file_path:
                file_data = read_file(file_path)
                tmp = fparser(file_data)
            self._cpath = file_path
            self._cdata = tmp
            return self._cdata

    state = State()
    return lambda self=None: state.get_values()


def parse_shaders(data):
    for (cid, cdata) in xray_io.ChunkedReader(data):
        if cid == 3:
            reader = xray_io.PackedReader(cdata)
            for _ in range(reader.int()):
                yield (reader.gets(), '', None)


def parse_gamemtl(data):
    for (cid, data) in xray_io.ChunkedReader(data):
        if cid == 4098:
            for (_, cdata) in xray_io.ChunkedReader(data):
                name, desc = None, None
                for (cccid, ccdata) in xray_io.ChunkedReader(cdata):
                    if cccid == 0x1000:
                        reader = xray_io.PackedReader(ccdata)
                        material_id = reader.getf('<I')[0]
                        name = reader.gets()
                    if cccid == 0x1005:
                        desc = xray_io.PackedReader(ccdata).gets()
                yield (name, desc, material_id)


def parse_shaders_xrlc(data):
    if len(data) % (128 + 16) != 0:
        exit(1)
    reader = xray_io.PackedReader(data)
    for _ in range(len(data) // (128 + 16)):
        name = reader.gets()
        reader.getf('{}s'.format(127 - len(name) + 16))  # skip
        yield (name, '', None)


HELPER_OBJECT_NAME_PREFIX = '.xray-helper--'


def is_helper_object(obj):
    if not obj:
        return False
    return obj.name.startswith(HELPER_OBJECT_NAME_PREFIX)


BAD_VTX_GROUP_NAME = '.xr-bad!'


def smooth_euler(current, previous):
    for axis in range(3):
        current[axis] = _smooth_angle(current[axis], previous[axis])


def _smooth_angle(current, previous):
    delta = abs(current - previous)
    new_delta = (current - 2 * math.pi) - previous
    if abs(new_delta) < delta:
        return previous + new_delta
    new_delta = (current + 2 * math.pi) - previous
    if abs(new_delta) < delta:
        return previous + new_delta
    return current


def mkstruct(name, fields):
    template = \
        'class {name}:\n' \
            '\t__slots__={fields}\n' \
            '\tdef __init__(self, {params}):\n' \
                '\t\t{params_init}={params}'.format(
        name=name,
        fields=fields,
        params=','.join(fields),
        params_init=','.join('self.' + field for field in fields)
    )
    tmp = {}
    exec(template, tmp)
    return tmp[name]


class InitializationContext:
    def __init__(self, operation):
        self.operation = operation
        self.plugin_version_number = plugin_version_number()
        self.thing = None


class ObjectSet:
    def __init__(self):
        self._set = set()

    def sync(self, objects, callback):
        _old = self._set
        if len(objects) == len(_old):
            return
        _new = set()
        for obj in objects:
            hsh = hash(obj)
            _new.add(hsh)
            if hsh not in _old:
                callback(obj)
        self._set = _new


class ObjectsInitializer:
    def __init__(self, keys):
        self._sets = [(key, ObjectSet()) for key in keys]

    def sync(self, operation, collections):
        ctx = InitializationContext(operation)

        def init_thing(thing):
            ctx.thing = thing
            # print('sync:', ctx.operation, ctx.thing)
            thing.xray.initialize(ctx)

        for key, objset in self._sets:
            things = getattr(collections, key)
            objset.sync(things, init_thing)


@contextlib.contextmanager
def using_mode(mode):
    if version_utils.IS_28:
        objects = bpy.context.view_layer.objects
    else:
        objects = bpy.context.scene.objects
    original = objects.active.mode
    bpy.ops.object.mode_set(mode=mode)
    try:
        yield
    finally:
        bpy.ops.object.mode_set(mode=original)


def execute_with_logger(method):
    def wrapper(self, context):
        try:
            name = self.__class__.bl_idname.replace('.', '_')
            with logger(name, self.report):
                return method(self, context)
        except AppError:
            return {'CANCELLED'}

    return wrapper


def execute_require_filepath(func):
    def wrapper(self, context):
        if not self.filepath:
            self.report({'ERROR'}, text.warn.no_file)
            return {'CANCELLED'}
        return func(self, context)

    return wrapper


def set_cursor_state(method):
    def wrapper(self, context):
        try:
            context.window.cursor_set('WAIT')
            return method(self, context)
        finally:
            context.window.cursor_set('DEFAULT')

    return wrapper


class FilenameExtHelper(bpy_extras.io_utils.ExportHelper):
    def export(self, context):
        pass

    @execute_with_logger
    @execute_require_filepath
    @set_cursor_state
    def execute(self, context):
        self.export(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.active_object:
            self.filepath = context.active_object.name
            if not self.filepath.lower().endswith(self.filename_ext):
                self.filepath += self.filename_ext
            return super().invoke(context, event)
        else:
            self.report({'ERROR'}, text.error.no_active_obj)
            return {'CANCELLED'}


def invoke_require_armature(func):
    def wrapper(self, context, event):
        active = context.active_object
        if not active:
            self.report({'ERROR'}, text.error.no_active_obj)
            return {'CANCELLED'}
        if active.type != 'ARMATURE':
            self.report({'ERROR'}, text.error.is_not_arm)
            return {'CANCELLED'}
        return func(self, context, event)

    return wrapper


def time_log():
    def decorator(func):
        name = func.__name__
        def wrap(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                log.debug('time', func=name, time=(time.time() - start))
        return wrap
    return decorator


def save_file(file_path, writer):
    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    try:
        with open(file_path, 'wb') as file:
            file.write(writer.data)
    except PermissionError:
        raise AppError(
            text.error.file_another_prog,
            log.props(file=os.path.basename(file_path), path=file_path)
        )


def read_file(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
    return data


def read_text_file(file_path):
    with open(file_path, mode='r', encoding='cp1251') as file:
        data = file.read()
    return data


# temporarily not used
def print_time_info(message=None, tabs_count=None, total_time=None):
    if not message:
        print()
        return
    if tabs_count:
        spaces = ' ' * 4 * tabs_count
    else:
        spaces = ''
    if total_time is None:
        print('{0}{1} start...'.format(spaces, message))
    else:
        message_text = '{0}{1: <50}'.format(spaces, message + ' end:')
        message_time = '{0:.6f} sec'.format(total_time)
        print('{0}{1}'.format(message_text, message_time))


def build_op_label(operator, compact=False):
    # build operator label
    if compact:
        prefix = ''
    else:
        prefix = 'X-Ray '
    label = '{0}{1} ({2})'.format(prefix, operator.text, operator.ext)
    return label


def get_revision_data(revision):
    preferences = version_utils.get_preferences()
    if preferences.custom_owner_name:
        curruser = preferences.custom_owner_name
    else:
        curruser = '\\\\{}\\{}'.format(platform.node(), getpass.getuser())
    currtime = int(time.time())
    if (not revision.owner) or (revision.owner == curruser):
        owner = curruser
        if revision.ctime:
            ctime = revision.ctime
        else:
            ctime = currtime
        moder = ''
        mtime = 0
    else:
        owner = revision.owner
        ctime = revision.ctime
        moder = curruser
        mtime = currtime
    return owner, ctime, moder, mtime


def is_armature_context(context):
    obj = context.object
    if not obj:
        return False
    return obj.type == 'ARMATURE'


def get_armature_object(bpy_obj):
    arm_mods = []    # armature modifiers
    armature = None
    for modifier in bpy_obj.modifiers:
        if (modifier.type == 'ARMATURE') and modifier.object:
            arm_mods.append(modifier)
    if len(arm_mods) == 1:
        modifier = arm_mods[0]
        if not modifier.show_viewport:
            log.warn(
                text.warn.object_arm_mod_disabled,
                object=bpy_obj.name,
                modifier=modifier.name
            )
        armature = modifier.object
    elif len(arm_mods) > 1:
        used_mods = []
        for modifier in arm_mods:
            if modifier.show_viewport:
                used_mods.append(modifier)
        if len(used_mods) > 1:
            raise AppError(
                text.error.object_many_arms,
                log.props(
                    root_object=bpy_obj.name,
                    armature_objects=[mod.object.name for mod in used_mods]
                )
            )
        else:
            armature = used_mods[0].object
    return armature


def get_chunks(data):
    chunked_reader = xray_io.ChunkedReader(data)
    chunks = {}
    for chunk_id, chunk_data in chunked_reader:
        if not chunks.get(chunk_id, None):
            chunks[chunk_id] = chunk_data
    return chunks


def find_root(obj):
    if obj.xray.isroot:
        return obj
    if obj.parent:
        return find_root(obj.parent)
    else:
        return obj


def get_selection_state(context):
    active_object = context.active_object
    selected_objects = set()
    for obj in context.selected_objects:
        selected_objects.add(obj)
    if active_object:
        mode = bpy.context.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode=mode)
    else:
        bpy.ops.object.select_all(action='DESELECT')
    return active_object, selected_objects


def set_selection_state(active_object, selected_objects):
    version_utils.set_active_object(active_object)
    for obj in selected_objects:
        version_utils.select_object(obj)


def set_mode(mode):
    if bpy.context.object:
        bpy.ops.object.mode_set(mode=mode)
