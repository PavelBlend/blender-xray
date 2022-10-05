# blender modules
import bpy

# addon modules
from .. import ui


CATEGORY = 'X-Ray'


def build_label(subtext=''):
    prefix = 'X-Ray Engine'
    return prefix + ': ' + subtext if subtext else prefix


class XRayPanel(bpy.types.Panel):
    bl_label = build_label()
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw_header(self, context):
        icon = ui.icons.get_stalker_icon()
        self.layout.label(icon_value=icon)
