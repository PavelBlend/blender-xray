from contextlib import contextmanager
import math
from . import log

def is_exportable_bone(bpy_bone):
    return bpy_bone.xray.exportable and not bpy_bone.name.endswith('.fake')


def find_bone_exportable_parent(bpy_bone):
    r = bpy_bone.parent
    while (r is not None) and not is_exportable_bone(r):
        r = r.parent
    return r


def version_to_number(major, minor, release):
    return ((major & 0xff) << 24) | ((minor & 0xff) << 16) | (release & 0xffff)


_plugin_version_number = 0
def plugin_version_number():
    global _plugin_version_number
    if _plugin_version_number == 0:
        from . import bl_info
        _plugin_version_number = version_to_number(*bl_info['version'])
    return _plugin_version_number


class AppError(Exception):
    def __init__(self, message, ctx=log.props()):
        super().__init__(message)
        self.ctx = ctx


@contextmanager
def logger(name, report):
    lgr = Logger(report)
    try:
        with log.using_logger(lgr):
            yield
    except AppError as err:
        lgr.warn(str(err), err.ctx)
        raise err
    finally:
        lgr.flush(name)


class Logger:
    def __init__(self, report):
        self._report = report
        self._full = list()

    def warn(self, message, ctx=None):
        message = str(message)
        message = message.strip()
        message = message[0].upper() + message[1:]
        self._full.append((message, ctx))

    def flush(self, logname='log'):
        uniq = dict()
        for msg, _ in self._full:
            uniq[msg] = uniq.get(msg, 0) + 1
        if not uniq:
            return

        lines = ['Digest:']
        for msg, cnt in uniq.items():
            line = msg
            if cnt > 1:
                line = ('[%dx] ' % cnt) + line
            lines.append(' ' + line)
            self._report({'WARNING'}, line)

        lines.extend(['', 'Full log:'])
        processed_groups = dict()
        last_line_is_message = False

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
                    lines.append('%s+-%s' % (prefix, group.data))
                    last_line_is_message = False
                    prefix += '|  '
                else:
                    prefix = ''
                processed_groups[group] = prefix
            return prefix


        last_message = None
        last_message_count = 0
        for msg, ctx in self._full:
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
        self._report({'WARNING'}, 'The full log was stored as \'%s\' (in the Text Editor)' % text.name)


def fix_ensure_lookup_table(bmv):
    if hasattr(bmv, 'ensure_lookup_table'):
        bmv.ensure_lookup_table()


def convert_object_to_space_bmesh(bpy_obj, space_matrix):
    import bmesh, bpy
    bm = bmesh.new()
    armmods = [m for m in bpy_obj.modifiers if m.type == 'ARMATURE' and m.show_viewport]
    try:
        for m in armmods:
            m.show_viewport = False
        bm.from_object(bpy_obj, bpy.context.scene)
    finally:
        for m in armmods:
            m.show_viewport = True
    mt = bpy_obj.matrix_world
    mt = space_matrix.inverted() * mt
    bm.transform(mt)
    need_flip = False
    for k in mt.to_scale():
        if k < 0:
            need_flip = not need_flip
    if need_flip:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)  # flip normals
    fix_ensure_lookup_table(bm.verts)
    return bm


def calculate_mesh_bbox(verts):
    def vf(va, vb, f):
        va.x = f(va.x, vb.x)
        va.y = f(va.y, vb.y)
        va.z = f(va.z, vb.z)

    fix_ensure_lookup_table(verts)
    mn = verts[0].co.copy()
    mx = mn.copy()

    for v in verts:
        vf(mn, v.co, min)
        vf(mx, v.co, max)

    return mn, mx


def gen_texture_name(tx, tx_folder):
    import os.path
    from bpy.path import abspath
    a_tx_fpath, a_tx_folder = os.path.normpath(abspath(tx.image.filepath)), os.path.abspath(tx_folder)
    a_tx_fpath = os.path.splitext(a_tx_fpath)[0]
    a_tx_fpath = a_tx_fpath[len(a_tx_folder):].replace(os.path.sep, '\\')
    if a_tx_fpath.startswith('\\'):
        a_tx_fpath = a_tx_fpath[1:]
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
                from io import open
                with open(fpath, mode='rb') as f:
                    tmp = fparser(f.read())
            self._cpath = fpath
            self._cdata = tmp
            return self._cdata

    state = State()
    return lambda self=None: state.get_values()


def parse_shaders(data):
    from .xray_io import ChunkedReader, PackedReader
    for (cid, data) in ChunkedReader(data):
        if cid == 3:
            pr = PackedReader(data)
            for i in range(pr.getf('I')[0]):
                yield (pr.gets(), '')


def parse_gamemtl(data):
    from .xray_io import ChunkedReader, PackedReader
    for (cid, data) in ChunkedReader(data):
        if cid == 4098:
            for (_, cdata) in ChunkedReader(data):
                name, desc = None, None
                for (cccid, ccdata) in ChunkedReader(cdata):
                    if cccid == 0x1000:
                        pr = PackedReader(ccdata)
                        pr.getf('I')[0]
                        name = pr.gets()
                    if cccid == 0x1005:
                        desc = PackedReader(ccdata).gets()
                yield (name, desc)


def parse_shaders_xrlc(data):
    from .xray_io import PackedReader
    if len(data) % (128 + 16) != 0:
        exit(1)
    pr = PackedReader(data)
    for _ in range(len(data) // (128 + 16)):
        n = pr.gets()
        pr.getf('{}s'.format(127 - len(n) + 16))  # skip
        yield (n, '')


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
