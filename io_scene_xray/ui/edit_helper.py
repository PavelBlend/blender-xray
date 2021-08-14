# blender modules
import bpy

# addon modules
from . import base
from .. import edit_helpers


class XRAY_PT_EditHelperObjectPanel(base.XRayPanel):
    bl_context = 'object'
    bl_label = base.build_label('Edit Helper')

    @classmethod
    def poll(cls, context):
        return edit_helpers.base.get_object_helper(context) is not None

    def draw(self, context):
        helper = edit_helpers.base.get_object_helper(context)
        helper.draw(self.layout, context)


def register():
    bpy.utils.register_class(XRAY_PT_EditHelperObjectPanel)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_EditHelperObjectPanel)
