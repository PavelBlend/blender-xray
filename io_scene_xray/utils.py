def is_fake_bone(bpy_bone):
    return bpy_bone.name.endswith('.fake')


def find_bone_real_parent(bpy_bone):
    r = bpy_bone.parent
    while (r is not None) and is_fake_bone(r):
        r = r.parent
    return r


def version_to_number(major, minor, release):
    return ((major & 0xff) << 24) | ((minor & 0xff) << 16) | (release & 0xffff)


class AppError(Exception):
    def __init__(self, message):
        super().__init__(message)


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

    mn = verts[0].co.copy()
    mx = mn.copy()

    for v in verts:
        vf(mn, v.co, min)
        vf(mx, v.co, max)

    return mn, mx


def gen_texture_name(tx, tx_folder):
    import os.path
    a_tx_fpath, a_tx_folder = os.path.abspath(tx.image.filepath), os.path.abspath(tx_folder)
    a_tx_fpath = os.path.splitext(a_tx_fpath)[0]
    return a_tx_fpath[len(a_tx_folder) + 1:].replace(os.path.sep, '\\')


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
