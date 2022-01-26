# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from .. import icons
from .. import utils
from .. import version_utils
from .. import ie_props


op_text = 'Error List'
filename_ext = '.err'

import_props = {
    'filepath': bpy.props.StringProperty(subtype="FILE_PATH"),
    'filter_glob': bpy.props.StringProperty(
        default='*.err', options={'HIDDEN'}
    )
}


class XRAY_OT_import_err(
        ie_props.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.err'
    bl_label = 'Import .err'
    bl_description = 'Imports X-Ray Error List (.err)'
    bl_options = {'REGISTER', 'UNDO'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = import_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        imp.import_file(self.filepath, self)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    version_utils.register_operators(XRAY_OT_import_err)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_import_err)
