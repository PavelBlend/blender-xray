# blender modules
import bpy


class InitPropGroup(bpy.types.PropertyGroup):
    ''' Base class for property group having initialization. '''

    def _during_creation(self):
        raise 'abstract'

    def initialize(self, operation, addon_ver):
        if not self.version:

            if operation == 'LOADED':
                self.version = -1

            elif operation == 'CREATED':
                self.version = addon_ver
                self._during_creation()


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
