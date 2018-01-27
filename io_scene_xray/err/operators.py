
import bpy
from bpy_extras import io_utils

from .. import registry
from . import imp


@registry.module_thing
class OpImportERR(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = 'xray_import.err'
    bl_label = 'Import .err'
    bl_description = 'Imports X-Ray Error List (.err)'
    bl_options = {'REGISTER', 'UNDO'}

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob = bpy.props.StringProperty(default='*.err', options={'HIDDEN'})

    def execute(self, context):
        imp.import_file(self.filepath, self)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func_import(self, _context):
    self.layout.operator(OpImportERR.bl_idname, text='X-Ray error list (.err)')


def register():
    bpy.types.INFO_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func_import)