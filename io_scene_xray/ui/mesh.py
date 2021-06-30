from . import base
from ..prefs.utils import get_preferences
from .. import registry
from ..utils import is_helper_object


@registry.module_thing
class XRAY_PT_MeshPanel(base.XRayPanel):
    bl_context = 'data'
    bl_label = base.build_label('Mesh')

    @classmethod
    def poll(cls, context):
        preferences = get_preferences()
        panel_used = (
            # import plugins
            preferences.enable_object_import or
            preferences.enable_level_import or
            # export plugins
            preferences.enable_object_export or
            preferences.enable_level_export
        )
        return (
            context.active_object and
            context.active_object.type in {'MESH'} and
            not is_helper_object(context.active_object) and
            get_preferences().expert_mode and
            panel_used
        )

    def draw(self, context):
        layout = self.layout
        data = context.object.data.xray
        row = layout.row(align=True)
        row.prop(data, 'flags_visible', text='Visible', toggle=True)
        row.prop(data, 'flags_locked', text='Locked', toggle=True)
        row.prop(data, 'flags_sgmask', text='SGMask', toggle=True)
