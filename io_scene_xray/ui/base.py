import bpy

from .. import plugin


def build_label(subtext=''):
    prefix = 'X-Ray Engine'
    return prefix + ': ' + subtext if subtext else prefix


class XRayPanel(bpy.types.Panel):
    bl_label = build_label()
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw_header(self, _context):
        self.layout.label(icon_value=plugin.get_stalker_icon())
