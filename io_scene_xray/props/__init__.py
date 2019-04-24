import bpy


def gen_flag_prop(mask, description='', customprop=''):
    def getter(self):
        return self.flags & mask

    def setter(self, value):
        self.flags = self.flags | mask if value else self.flags & ~mask
        if customprop and hasattr(self, customprop):
            setattr(self, customprop, True)

    return bpy.props.BoolProperty(
        description=description,
        get=getter, set=setter,
        options={'SKIP_SAVE'}
    )


from . import obj
from . import mesh
from . import material
from . import armature
from . import bone
from . import action
from . import scene
