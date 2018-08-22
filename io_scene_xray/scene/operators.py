
import bpy
from bpy_extras import io_utils

from .. import utils


class OpExportLevelScene(bpy.types.Operator, io_utils.ExportHelper):

    bl_idname = 'xray_export.scene'
    bl_label = 'Export .level'

    filename_ext = '.level'

    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
        )

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


def menu_func_export(self, context):
    self.layout.operator(OpExportLevelScene.bl_idname, text='X-Ray level scene (.level)')


def register_operators():
    bpy.utils.register_class(OpExportLevelScene)


def unregister_operators():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(OpExportLevelScene)
