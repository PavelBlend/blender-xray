# blender modules
import bpy

# addon modules
from .. import ui
from .. import obj
from .. import utils


class XRAY_PT_scene(ui.base.XRayPanel):
    bl_context = 'scene'
    bl_label = ui.base.build_label('Project')

    @classmethod
    def poll(cls, context):
        preferences = utils.version.get_preferences()
        panel_used = (
            # import plugins
            preferences.enable_object_import or
            # export plugins
            preferences.enable_object_export
        )
        return panel_used

    def draw(self, context):
        scn = context.scene
        data = scn.xray

        def gen_op(layout, text, enabled=True, icon='NONE'):
            if not enabled:
                layout = layout.split()
                layout.enabled = False
            props = layout.operator(
                obj.exp.ops.XRAY_OT_export_project.bl_idname,
                text=text,
                icon=icon
            )
            return props

        layout = self.layout
        row = layout.row()
        if not data.export_root:
            row.enabled = False
        selection = obj.exp.ops.XRAY_OT_export_project.find_objects(
            context,
            use_selection=True
        )
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
        scene = obj.exp.ops.XRAY_OT_export_project.find_objects(context)
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
        row = utils.version.layout_split(layout, 0.33)
        row.label(text='Format Version:')
        row.row().prop(data, 'fmt_version', expand=True)
        _, box = ui.collapsible.draw(layout, 'scene:object', 'Object Export Properties')
        if box:
            box.prop(data, 'object_export_motions')
            box.prop(data, 'object_texture_name_from_image_path')


def register():
    bpy.utils.register_class(XRAY_PT_scene)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_scene)
