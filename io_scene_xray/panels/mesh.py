# blender modules
import bpy

# addon modules
from .. import ui
from .. import utils


class XRAY_PT_mesh(ui.base.XRayPanel):
    bl_context = 'data'
    bl_label = ui.base.build_label('Mesh')

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if not obj:
            return

        if obj.type != 'MESH':
            return

        is_helper = utils.obj.is_helper_object(obj)
        if is_helper:
            return

        pref = utils.version.get_preferences()

        panel_used = (
            # import formats
            pref.enable_object_import or
            pref.enable_scene_import or
            pref.enable_part_import or
            pref.enable_group_import or

            # export formats
            pref.enable_object_export or
            pref.enable_scene_export or
            pref.enable_part_export or
            pref.enable_group_export
        )

        return panel_used

    def draw(self, context):
        row = self.layout.row(align=True)
        data = context.active_object.data.xray

        row.prop(data, 'flags_visible', text='Visible', toggle=True)
        row.prop(data, 'flags_locked', text='Locked', toggle=True)
        row.prop(data, 'flags_sgmask', text='SGMask', toggle=True)


def register():
    bpy.utils.register_class(XRAY_PT_mesh)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_mesh)
