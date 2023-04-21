# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from .. import ie
from ... import log
from ... import utils


op_text = 'Error List'
filename_ext = '.err'

import_props = {
    'filepath': bpy.props.StringProperty(
        subtype="FILE_PATH", options={'HIDDEN'}
    ),
    'filter_glob': bpy.props.StringProperty(
        default='*.err', options={'HIDDEN'}
    )
}


class XRAY_OT_import_err(
        utils.ie.BaseOperator,
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

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        imp.import_file(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    utils.version.register_operators(XRAY_OT_import_err)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_import_err)
