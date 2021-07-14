import bpy
from bpy_extras import io_utils

from ..ops.base import BaseOperator as TestReadyOperator
from .. import ui, utils
from . import imp
from ..version_utils import get_import_export_menus, assign_props, IS_28


op_import_err_props = {
    'filepath': bpy.props.StringProperty(subtype="FILE_PATH"),
    'filter_glob': bpy.props.StringProperty(default='*.err', options={'HIDDEN'})
}


class OpImportERR(TestReadyOperator, io_utils.ImportHelper):
    bl_idname = 'xray_import.err'
    bl_label = 'Import .err'
    bl_description = 'Imports X-Ray Error List (.err)'
    bl_options = {'REGISTER', 'UNDO'}

    if not IS_28:
        for prop_name, prop_value in op_import_err_props.items():
            exec('{0} = op_import_err_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):
        imp.import_file(self.filepath, self)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func_import(self, _context):
    icon = ui.icons.get_stalker_icon()
    self.layout.operator(
        OpImportERR.bl_idname,
        text='X-Ray error list (.err)',
        icon_value=icon
        )


def register():
    assign_props([(op_import_err_props, OpImportERR), ])
    bpy.utils.register_class(OpImportERR)


def unregister():
    import_menu, _ = get_import_export_menus()
    import_menu.remove(menu_func_import)
    bpy.utils.unregister_class(OpImportERR)
