# blender modules
import bpy
import bpy_extras

# addon modules
from . import exp
from .. import icons
from .. import contexts
from .. import version_utils
from .. import plugin_props
from .. import utils


def menu_func_export(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_ogf.bl_idname,
        text=utils.build_op_label(XRAY_OT_export_ogf),
        icon_value=icon
    )


class ExportOgfContext(contexts.ExportMeshContext):
    def __init__(self):
        contexts.ExportMeshContext.__init__(self)


op_text = 'Game Object'
filename_ext = '.ogf'

op_export_ogf_props = {
    'filter_glob': bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'}),
    'texture_name_from_image_path': plugin_props.PropObjectTextureNamesFromPath()
}


class XRAY_OT_export_ogf(
        plugin_props.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.ogf'
    bl_label = 'Export .ogf'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    draw_fun = menu_func_export
    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_ogf_props.items():
            exec('{0} = op_export_ogf_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.execute_require_filepath
    @utils.set_cursor_state
    def execute(self, context):
        export_context = ExportOgfContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        exp.export_file(self.exported_object, self.filepath, export_context)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.texture_name_from_image_path = preferences.object_texture_names_from_path
        self.filepath = context.object.name
        objs = context.selected_objects
        roots = [obj for obj in objs if obj.xray.isroot]
        if not roots:
            self.report({'ERROR'}, 'Cannot find object root')
            return {'CANCELLED'}
        if len(roots) > 1:
            self.report({'ERROR'}, 'Too many object roots found')
            return {'CANCELLED'}
        self.exported_object = roots[0]
        return super().invoke(context, event)


def register():
    version_utils.assign_props([
        (op_export_ogf_props, XRAY_OT_export_ogf)
    ])
    bpy.utils.register_class(XRAY_OT_export_ogf)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_export_ogf)
