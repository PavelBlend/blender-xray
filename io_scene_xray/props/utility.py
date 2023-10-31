# blender modules
import bpy


def gen_flag_prop(mask, description='', custom_prop=''):

    def getter(self):
        return bool(self.flags & mask)

    def setter(self, value):
        if value:
            self.flags |= mask
        else:
            self.flags &= ~mask

        if custom_prop and hasattr(self, custom_prop):
            setattr(self, custom_prop, True)

    return bpy.props.BoolProperty(
        description=description,
        get=getter,
        set=setter,
        options={'SKIP_SAVE'}
    )
