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
