import bpy
from bpy_extras import io_utils

from .. import utils, plugin
from ..utils import AppError
from .. import plugin_prefs
from .imp import import_file


class OpExportLevelScene(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = 'xray_export.scene'
    bl_label = 'Export .level'

    filename_ext = '.level'

    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
        )

    @utils.set_cursor_state
    def execute(self, context):

        try:
            self.export(self.objs, context)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        return {'FINISHED'}

    def export(self, bpy_objs, context):

        from .exp import export_file

        export_file(bpy_objs, self.filepath)

    def invoke(self, context, event):

        self.objs = context.selected_objects

        if not self.objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}

        return super().invoke(context, event)


class OpImportLevelScene(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = 'xray_import.scene'
    bl_label = 'Import .level'
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.level'

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
        )

    mesh_split_by_materials = plugin_prefs.PropObjectMeshSplitByMaterials()
    fmt_version = plugin_prefs.PropSDKVersion()

    def draw(self, _context):
        layout = self.layout

        row = layout.split()
        row.label('Format Version:')
        row.row().prop(self, 'fmt_version', expand=True)

        layout.prop(self, 'mesh_split_by_materials')

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        try:
            import_file(self.filepath, self)
        except AppError as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func_export(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        OpExportLevelScene.bl_idname,
        text='X-Ray scene selection (.level)',
        icon_value=icon
        )


def menu_func_import(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        OpImportLevelScene.bl_idname,
        text='X-Ray scene selection (.level)',
        icon_value=icon
        )


def register_operators():
    bpy.utils.register_class(OpExportLevelScene)
    bpy.utils.register_class(OpImportLevelScene)


def unregister_operators():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(OpExportLevelScene)
    bpy.utils.unregister_class(OpImportLevelScene)
