# blender modules
import bpy

# addon modules
from .. import ui
from .. import formats
from .. import utils


def gen_op(layout, text, enabled=True, icon='NONE'):
    if not enabled:
        layout = layout.split()
        layout.enabled = False
    props = layout.operator(
        formats.obj.exp.ops.XRAY_OT_export_project.bl_idname,
        text=text,
        icon=icon
    )
    return props


class XRAY_PT_scene(ui.base.XRayPanel):
    bl_context = 'scene'
    bl_label = ui.base.build_label('Project')

    @classmethod
    def poll(cls, context):
        pref = utils.version.get_preferences()

        panel_used = pref.enable_object_export

        return panel_used

    def draw(self, context):
        scn = context.scene
        data = scn.xray

        layout = self.layout

        # export directory
        lay = layout

        if not data.export_root:
            lay = lay.split()
            lay.alert = True

        lay.prop(data, 'export_root')

        col = layout.column()
        if not data.export_root:
            col.enabled = False

        # export properties
        box = col.box()
        box.label(text='Export Properties:')

        utils.draw.draw_fmt_ver_prop(box, data, 'fmt_version')

        row = box.split()
        row.label(text='Smoothing:')
        row.row().prop(data, 'smoothing_out_of', expand=True)

        box.prop(data, 'object_export_motions')
        box.prop(data, 'use_export_paths')
        box.prop(data, 'object_texture_name_from_image_path')

        # export operators
        operator = formats.obj.exp.ops.XRAY_OT_export_project

        # export selected
        selection = operator.find_objects(context, use_selection=True)

        if not selection:
            gen_op(col, 'No Roots Selected', enabled=False)

        elif len(selection) == 1:
            gen_op(
                col,
                text=selection[0].name + '.object',
                icon='OUTLINER_OB_MESH'
            ).use_selection = True

        else:
            gen_op(
                col,
                text='Selected Objects ({})'.format(len(selection)),
                icon='GROUP'
            ).use_selection = True

        # export scene
        scene = operator.find_objects(context)

        gen_op(
            col,
            text='Scene Export ({})'.format(len(scene)),
            icon='SCENE_DATA',
            enabled=len(scene) != 0
        ).use_selection = False


def register():
    bpy.utils.register_class(XRAY_PT_scene)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_scene)
