import bpy

from . import verify_uv
from .. import plugin
from ..version_utils import IS_28


class XRAY_PT_VerifyToolsPanel(bpy.types.Panel):
    bl_label = 'XRay Verify'
    bl_space_type = 'VIEW_3D'
    bl_category = 'XRay'
    if IS_28:
        bl_region_type = 'UI'
    else:
        bl_region_type = 'TOOLS'

    def draw_header(self, _context):
        icon = plugin.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        data = context.scene.xray
        layout = self.layout
        layout.operator(verify_uv.XRayVerifyUVOperator.bl_idname, icon='GROUP_UVS')
