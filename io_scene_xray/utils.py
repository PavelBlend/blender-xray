from contextlib import contextmanager
import math, os
from time import time

from bpy_extras import io_utils

from . import log
from .version_utils import IS_28, multiply


__FAKE_BONE_SUFFIX = '.fake'

def is_fake_bone_name(bone_name):
    return bone_name.endswith(__FAKE_BONE_SUFFIX)

def build_fake_bone_name(bone_name):
    return bone_name + __FAKE_BONE_SUFFIX

def is_exportable_bone(bpy_bone):
    return bpy_bone.xray.exportable and not is_fake_bone_name(bpy_bone.name)


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
        from . import bl_info
        number = version_to_number(*bl_info['version'])
        __PLUGIN_VERSION_NUMBER__[0] = number
    return number


class AppError(Exception):
    def __init__(self, message, ctx=None):
        if ctx is None:
            ctx = log.props()
        super().__init__(message)
        self.ctx = ctx


@contextmanager
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
        for msg, _, typ in self._full:
            uniq[msg] = uniq.get(msg, (0, typ))[0] + 1, typ
        if not uniq:
            return

        lines = ['Digest:']
        for msg, (cnt, typ) in uniq.items():
            line = msg
            if cnt > 1:
                line = ('[%dx] ' % cnt) + line
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
                msg += (': %s' % data)
            if last_line_is_message and (last_message == msg):
                last_message_count += 1
                lines[-1] = '%s[%dx] %s' % (prefix, last_message_count, msg)
            else:
                lines.append(prefix + msg)
                last_message = msg
                last_message_count = 1
                last_line_is_message = True

        import bpy
        text = bpy.data.texts.new(logname)
        text.user_clear()
        text.from_string('\n'.join(lines))
        self._report(
            {'WARNING'},
            'The full log was stored as \'%s\' (in the Text Editor)' % text.name
        )


def fix_ensure_lookup_table(bmv):
    if hasattr(bmv, 'ensure_lookup_table'):
        bmv.ensure_lookup_table()


def convert_object_to_space_bmesh(bpy_obj, space_matrix, local=False):
    import bmesh
    import bpy
    import mathutils
    mesh = bmesh.new()
    armmods = [mod for mod in bpy_obj.modifiers if mod.type == 'ARMATURE' and mod.show_viewport]
    try:
        for mod in armmods:
            mod.show_viewport = False
        if IS_28:
            mesh.from_object(bpy_obj, bpy.context.view_layer.depsgraph)
        else:
            mesh.from_object(bpy_obj, bpy.context.scene)
    finally:
        for mod in armmods:
            mod.show_viewport = True
    if local:
        mat = mathutils.Matrix()
    else:
        mat = bpy_obj.matrix_world
    mat = multiply(space_matrix.inverted(), mat)
    mesh.transform(mat)
    need_flip = False
    for k in mat.to_scale():
        if k < 0:
            need_flip = not need_flip
    if need_flip:
        bmesh.ops.reverse_faces(mesh, faces=mesh.faces)  # flip normals
    fix_ensure_lookup_table(mesh.verts)
    return mesh


def calculate_mesh_bbox(verts):
    def vfunc(dst, src, func):
        dst.x = func(dst.x, src.x)
        dst.y = func(dst.y, src.y)
        dst.z = func(dst.z, src.z)

    fix_ensure_lookup_table(verts)
    _min = verts[0].co.copy()
    _max = _min.copy()

    for vertex in verts:
        vfunc(_min, vertex.co, min)
        vfunc(_max, vertex.co, max)

    return _min, _max


def make_relative_texture_path(a_tx_fpath, a_tx_folder):
    a_tx_fpath = a_tx_fpath[len(a_tx_folder):].replace(os.path.sep, '\\')
    if a_tx_fpath.startswith('\\'):
        a_tx_fpath = a_tx_fpath[1:]
    return a_tx_fpath


def gen_texture_name(texture, tx_folder, mode='DEFAULT'):
    from bpy.path import abspath
    a_tx_fpath = os.path.normpath(abspath(texture.image.filepath))
    a_tx_folder = os.path.abspath(tx_folder)
    a_tx_fpath = os.path.splitext(a_tx_fpath)[0]
    if mode == 'DEFAULT':    # find texture in gamedata\textures folder
        a_tx_fpath = make_relative_texture_path(a_tx_fpath, a_tx_folder)
    elif mode == 'DETAILS':
        if a_tx_fpath.startswith(a_tx_folder):    # gamedata\textures folder
            a_tx_fpath = make_relative_texture_path(a_tx_fpath, a_tx_folder)
        else:    # gamedata\levels\level_name folder
            a_tx_fpath = os.path.split(a_tx_fpath)[-1]
    else:
        raise BaseException('Unknown generate texture name mode: {}'.format(mode))
    return a_tx_fpath


def create_cached_file_data(ffname, fparser):
    class State:
        def __init__(self):
            self._cdata = None
            self._cpath = None

        def get_values(self):
            fpath = ffname()
            if self._cpath == fpath:
                return self._cdata
            tmp = None
            if fpath:
                with open(fpath, mode='rb') as file:
                    tmp = fparser(file.read())
            self._cpath = fpath
            self._cdata = tmp
            return self._cdata

    state = State()
    return lambda self=None: state.get_values()


def parse_shaders(data):
    from .xray_io import ChunkedReader, PackedReader
    for (cid, cdata) in ChunkedReader(data):
        if cid == 3:
            reader = PackedReader(cdata)
            for _ in range(reader.int()):
                yield (reader.gets(), '')


def parse_gamemtl(data):
    from .xray_io import ChunkedReader, PackedReader
    for (cid, data) in ChunkedReader(data):
        if cid == 4098:
            for (_, cdata) in ChunkedReader(data):
                name, desc = None, None
                for (cccid, ccdata) in ChunkedReader(cdata):
                    if cccid == 0x1000:
                        reader = PackedReader(ccdata)
                        reader.skip(4)
                        name = reader.gets()
                    if cccid == 0x1005:
                        desc = PackedReader(ccdata).gets()
                yield (name, desc)


def parse_shaders_xrlc(data):
    from .xray_io import PackedReader
    if len(data) % (128 + 16) != 0:
        exit(1)
    reader = PackedReader(data)
    for _ in range(len(data) // (128 + 16)):
        name = reader.gets()
        reader.getf('{}s'.format(127 - len(name) + 16))  # skip
        yield (name, '')


HELPER_OBJECT_NAME_PREFIX = '.xray-helper--'


def is_helper_object(obj):
    return obj.name.startswith(HELPER_OBJECT_NAME_PREFIX)

BAD_VTX_GROUP_NAME = '.xr-bad!'


def smooth_euler(current, previous):
    for i in range(3):
        current[i] = _smooth_angle(current[i], previous[i])


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
    template = 'class {n}:\n\t__slots__={f}\n\tdef __init__(self, {a}):\n\t\t{sf}={a}'\
    .format(
        n=name, f=fields, a=','.join(fields),
        sf=','.join('self.' + f for f in fields)
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

@contextmanager
def using_mode(mode):
    import bpy
    original = bpy.context.object.mode
    bpy.ops.object.mode_set(mode=mode)
    try:
        yield
    finally:
        bpy.ops.object.mode_set(mode=original)

def with_auto_property(prop_class, prop_id, getter, overrides=None, **kwargs):
    def decorator(struct):
        if IS_28:
            if hasattr(struct, '__annotations__'):
                struct.__annotations__[prop_id] = prop_class(**kwargs)
            else:
                struct.__annotations__ = {prop_id: prop_class(**kwargs), }
        else:
            setattr(struct, prop_id, prop_class(
                **kwargs,
            ))

        def get_value(self):
            value = getattr(self, prop_id)
            if not value:
                value = getter(self)
            return value

        def set_value(self, value):
            org_value = get_value(self)
            if value != org_value:
                setattr(self, prop_id, value)

        kwargs2 = dict(kwargs)
        if 'name' in kwargs2:
            kwargs2['name'] += ' (auto)'
        if 'description' in kwargs2:
            kwargs2['description'] += ' (automatically calculated value)'
        if overrides:
            kwargs2 = {**kwargs2, **overrides}

        if IS_28:
            struct.__annotations__[with_auto_property.build_auto_id(prop_id)] = prop_class(
                **kwargs2, get=get_value, set=set_value
            )
        else:
            setattr(struct, with_auto_property.build_auto_id(prop_id), prop_class(
                **kwargs2,
                get=get_value,
                set=set_value,
            ))
        return struct

    return decorator
with_auto_property.build_auto_id = lambda id: id + '_auto'


def execute_with_logger(method):
    def wrapper(self, context):
        try:
            with logger(self.__class__.bl_idname, self.report):
                return method(self, context)
        except AppError:
            return {'CANCELLED'}

    return wrapper


def execute_require_filepath(func):
    def wrapper(self, context):
        if not self.filepath:
            self.report({'ERROR'}, 'No file selected')
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


class FilenameExtHelper(io_utils.ExportHelper):
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
            self.report({'ERROR'}, 'No active objects')
            return {'CANCELLED'}


def invoke_require_armature(func):
    def wrapper(self, context, event):
        active = context.active_object
        if (not active) or (active.type != 'ARMATURE'):
            self.report({'ERROR'}, 'Active is not armature')
            return {'CANCELLED'}
        return func(self, context, event)

    return wrapper


def mk_export_context(texname_from_path, fmt_version=None, export_motions=True):
    from .obj.exp import ExportContext
    from . import plugin_prefs
    return ExportContext(
        textures_folder=plugin_prefs.get_preferences().textures_folder_auto,
        export_motions=export_motions,
        soc_sgroups=None if fmt_version is None else (fmt_version == 'soc'),
        texname_from_path=texname_from_path
    )

def time_log():
    def decorator(func):
        name = func.__name__
        def wrap(*args, **kwargs):
            start = time()
            try:
                return func(*args, **kwargs)
            finally:
                log.debug('time', func=name, time=(time() - start))
        return wrap
    return decorator


def save_file(file_path, writer):
    with open(file_path, 'wb') as file:
        file.write(writer.data)
