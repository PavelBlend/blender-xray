# blender modules
import bpy

# addon modules
from .. import ui
from .. import version_utils
from .. import utils


class XRAY_PT_mesh(ui.base.XRayPanel):
    bl_context = 'data'
    bl_label = ui.base.build_label('Mesh')

    @classmethod
    def poll(cls, context):
        preferences = version_utils.get_preferences()
        panel_used = (
            # import plugins
            preferences.enable_object_import or
            preferences.enable_level_import or
            # export plugins
            preferences.enable_object_export or
            preferences.enable_level_export
        )
        if not panel_used:
            return False
        bpy_obj = context.active_object
        if not bpy_obj:
            return False
        if not bpy_obj.type == 'MESH':
            return False
        is_helper = utils.is_helper_object(bpy_obj)
        if is_helper:
            return False
        return True

    def draw(self, context):
        layout = self.layout
        data = context.object.data.xray
        row = layout.row(align=True)
        row.prop(data, 'flags_visible', text='Visible', toggle=True)
        row.prop(data, 'flags_locked', text='Locked', toggle=True)
        row.prop(data, 'flags_sgmask', text='SGMask', toggle=True)


def register():
    bpy.utils.register_class(XRAY_PT_mesh)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_mesh)
