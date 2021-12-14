# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import utils
from .. import icons
from .. import log
from .. import ie_props
from .. import version_utils


def menu_func_export(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_scene_selection.bl_idname,
        text=utils.build_op_label(XRAY_OT_export_scene_selection),
        icon_value=icon
    )


def menu_func_import(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_import_scene_selection.bl_idname,
        text=utils.build_op_label(XRAY_OT_import_scene_selection),
        icon_value=icon
    )


op_text = 'Scene Selection'
filename_ext = '.level'

op_export_level_scene_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
    ),
}


class XRAY_OT_export_scene_selection(
        ie_props.BaseOperator, bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.scene'
    bl_label = 'Export .level'

    draw_fun = menu_func_export
    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_level_scene_props.items():
            exec('{0} = op_export_level_scene_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        try:
            self.export(self.objs, context)
        except utils.AppError as err:
            log.err(err)
        return {'FINISHED'}

    def export(self, bpy_objs, context):
        exp.export_file(bpy_objs, self.filepath)

    def invoke(self, context, event):

        self.objs = context.selected_objects

        if not self.objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}

        return super().invoke(context, event)


op_import_level_scene_props = {
    'filepath': bpy.props.StringProperty(subtype="FILE_PATH"),
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
    ),
    'mesh_split_by_materials': ie_props.PropObjectMeshSplitByMaterials(),
    'fmt_version': ie_props.PropSDKVersion()
}


class XRAY_OT_import_scene_selection(
        ie_props.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.scene'
    bl_label = 'Import .level'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    draw_fun = menu_func_import
    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_import_level_scene_props.items():
            exec('{0} = op_import_level_scene_props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout

        row = layout.split()
        row.label(text='Format Version:')
        row.row().prop(self, 'fmt_version', expand=True)

        layout.prop(self, 'mesh_split_by_materials')

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        try:
            imp.import_file(self.filepath, self)
        except utils.AppError as err:
            log.err(err)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.mesh_split_by_materials = preferences.scene_selection_mesh_split_by_mat
        self.fmt_version = preferences.scene_selection_sdk_version
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    version_utils.assign_props([
        (op_export_level_scene_props, XRAY_OT_export_scene_selection),
        (op_import_level_scene_props, XRAY_OT_import_scene_selection)
    ])
    bpy.utils.register_class(XRAY_OT_export_scene_selection)
    bpy.utils.register_class(XRAY_OT_import_scene_selection)


def unregister():
    import_menu, export_menu = version_utils.get_import_export_menus()
    export_menu.remove(menu_func_export)
    import_menu.remove(menu_func_import)
    bpy.utils.unregister_class(XRAY_OT_export_scene_selection)
    bpy.utils.unregister_class(XRAY_OT_import_scene_selection)
