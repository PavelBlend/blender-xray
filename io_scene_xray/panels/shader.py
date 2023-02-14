# blender modules
import bpy

# addon modules
from .. import ui
from .. import ops


class XRAY_PT_shader(ui.base.XRayPanel):
    bl_space_type = 'NODE_EDITOR'
    bl_label = 'Shader'
    bl_category = ui.base.CATEGORY
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return

        return obj.active_material

    def draw(self, context):
        lay = self.layout
        obj = context.active_object
        mat = obj.active_material

        op = lay.operator(ops.material.XRAY_OT_create_material.bl_idname)
        op.material_name = mat.name


def register():
    bpy.utils.register_class(XRAY_PT_shader)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_shader)
