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
        obj = context.object
        if not obj:
            return False
        mat = obj.active_material
        return bool(mat)

    def draw(self, context):
        layout = self.layout
        operator = layout.operator(ops.material.XRAY_OT_create_material.bl_idname)
        obj = context.object
        mat = obj.active_material
        operator.material_name = mat.name


def register():
    bpy.utils.register_class(XRAY_PT_shader)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_shader)
