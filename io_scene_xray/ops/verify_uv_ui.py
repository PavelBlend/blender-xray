
import bpy

from . import verify_uv
from .. import plugin


class XRayVerifyToolsPanel(bpy.types.Panel):
    bl_label = 'XRay Verify'
    bl_category = 'XRay'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw_header(self, _context):
        icon = plugin.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        data = context.scene.xray
        layout = self.layout
        layout.operator(verify_uv.XRayVerifyUVOperator.bl_idname, icon='GROUP_UVS')
