# blender modules
import bpy

# addon modules
from .. import ui
from .. import ops


class XRAY_PT_edit_helper(ui.base.XRayPanel):
    bl_context = 'object'
    bl_label = ui.base.build_label('Edit Helper')

    @classmethod
    def poll(cls, context):
        return ops.edit_helpers.base.get_object_helper(context) is not None

    def draw(self, context):
        helper = ops.edit_helpers.base.get_object_helper(context)
        helper.draw(self.layout, context)


def register():
    bpy.utils.register_class(XRAY_PT_edit_helper)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_edit_helper)
