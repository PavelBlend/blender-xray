# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from .. import icons
from .. import utils
from .. import version_utils
from .. import plugin_props


def menu_func_import(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_import_err.bl_idname,
        text=utils.build_op_label(XRAY_OT_import_err),
        icon_value=icon
    )


op_text = 'Error List'
filename_ext = '.err'

op_import_err_props = {
    'filepath': bpy.props.StringProperty(subtype="FILE_PATH"),
    'filter_glob': bpy.props.StringProperty(
        default='*.err', options={'HIDDEN'}
    )
}


class XRAY_OT_import_err(
        plugin_props.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.err'
    bl_label = 'Import .err'
    bl_description = 'Imports X-Ray Error List (.err)'
    bl_options = {'REGISTER', 'UNDO'}

    draw_fun = menu_func_import
    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_import_err_props.items():
            exec('{0} = op_import_err_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):
        imp.import_file(self.filepath, self)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    version_utils.assign_props([(op_import_err_props, XRAY_OT_import_err), ])
    bpy.utils.register_class(XRAY_OT_import_err)


def unregister():
    import_menu, _ = version_utils.get_import_export_menus()
    import_menu.remove(menu_func_import)
    bpy.utils.unregister_class(XRAY_OT_import_err)
