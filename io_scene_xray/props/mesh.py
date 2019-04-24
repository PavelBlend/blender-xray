import bpy

from .. import props


def gen_other_flags_prop(mask):
    def getter(self):
        return self.flags & mask

    def setter(self, value):
        self.flags = (self.flags & ~mask) | (value & mask)

    return bpy.props.IntProperty(get=getter, set=setter, options={'SKIP_SAVE'})


class XRayMeshProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Mesh
    flags = bpy.props.IntProperty(name='flags', default=0x1)
    flags_visible = props.gen_flag_prop(mask=0x01)
    flags_locked = props.gen_flag_prop(mask=0x02)
    flags_sgmask = props.gen_flag_prop(mask=0x04)
    # flags_other = gen_other_flags_prop(mask=~0x01)
