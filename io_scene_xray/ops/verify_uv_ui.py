
import bpy

from . import verify_uv


class XRayVerifyToolsPanel(bpy.types.Panel):
    bl_label = 'XRay Verify'
    bl_category = 'XRay'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw_header(self, _context):
        self.layout.label(icon='PLUGIN')

    def draw(self, context):
        data = context.scene.xray
        layout = self.layout
        layout.operator(verify_uv.XRayVerifyUVOperator.bl_idname, icon='GROUP_UVS')
