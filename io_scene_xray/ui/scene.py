from .. import registry, plugin_prefs
from ..plugin import OpExportProject
from .base import XRayPanel, build_label
from . import collapsible
from ..version_utils import layout_split


@registry.module_thing
class XRAY_PT_ScenePanel(XRayPanel):
    bl_context = 'scene'
    bl_label = build_label('Project')

    @classmethod
    def poll(cls, context):
        prefs = plugin_prefs.get_preferences()
        panel_used = (
            # import plugins
            prefs.enable_object_import or
            # export plugins
            prefs.enable_object_export
        )
        return panel_used

    def draw(self, context):
        obj = context.scene
        data = obj.xray

        def gen_op(layout, text, enabled=True, icon='NONE'):
            if not enabled:
                layout = layout.split()
                layout.enabled = False
            props = layout.operator(OpExportProject.bl_idname, text=text, icon=icon)
            return props

        layout = self.layout
        row = layout.row()
        if not data.export_root:
            row.enabled = False
        selection = OpExportProject.find_objects(context, use_selection=True)
        if not selection:
            gen_op(row, 'No Roots Selected', enabled=False)
        elif len(selection) == 1:
            gen_op(
                row,
                text=selection[0].name + '.object',
                icon='OUTLINER_OB_MESH'
            ).use_selection = True
        else:
            gen_op(
                row,
                text='Selected Objects (%d)' % len(selection),
                icon='GROUP'
            ).use_selection = True
        scene = OpExportProject.find_objects(context)
        gen_op(
            row,
            text='Scene Export (%d)' % len(scene),
            icon='SCENE_DATA',
            enabled=len(scene) != 0
        ).use_selection = False
        lay = layout
        if not data.export_root:
            lay = lay.split()
            lay.alert = True
        lay.prop(data, 'export_root')
        row = layout_split(layout, 0.33)
        row.label(text='Format Version:')
        row.row().prop(data, 'fmt_version', expand=True)
        _, box = collapsible.draw(layout, 'scene:object', 'Object Export Properties')
        if box:
            box.prop(data, 'object_export_motions')
            box.prop(data, 'object_texture_name_from_image_path')
