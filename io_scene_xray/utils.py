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


def convert_object_to_worldspace_bmesh(bpy_obj):
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
