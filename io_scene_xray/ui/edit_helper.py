import bpy

from .base import XRayPanel, build_label
from ..edit_helpers import base as base_edit_helper


class XRAY_PT_EditHelperObjectPanel(XRayPanel):
    bl_context = 'object'
    bl_label = build_label('Edit Helper')

    @classmethod
    def poll(cls, context):
        return base_edit_helper.get_object_helper(context) is not None

    def draw(self, context):
        helper = base_edit_helper.get_object_helper(context)
        helper.draw(self.layout, context)


def register():
    bpy.utils.register_class(XRAY_PT_EditHelperObjectPanel)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_EditHelperObjectPanel)
