# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import ie
from .. import contexts
from ... import utils
from ... import text
from ... import log


class ImportLevelContext(contexts.ImportMeshContext):
    pass


if utils.version.broken_file_browser_filter():
    file_filter_import = '*'
else:
    file_filter_import = 'level'


import_props = {
    'filter_glob': bpy.props.StringProperty(
        default=file_filter_import,
        options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH",
        options={'HIDDEN'}
    ),
    'filepath': bpy.props.StringProperty(
        subtype="FILE_PATH",
        options={'SKIP_SAVE', 'HIDDEN'}
    ),
    'processed': bpy.props.BoolProperty(default=False, options={'HIDDEN'})
}


class XRAY_OT_import_level(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.level'
    bl_label = 'Import level'
    bl_description = 'Import X-Ray Game Level (level)'
    bl_options = {'REGISTER', 'UNDO'}

    text = 'Game Level'
    filename_ext = ''
    ext = 'level'
    props = import_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'levels_folder')

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, 'No file selected')
            return {'CANCELLED'}
        import_context = ImportLevelContext()
        import_context.operator=self
        import_context.filepath = self.filepath
        try:
            imp.import_file(import_context)
        except log.AppError as err:
            import_context.errors.append(err)
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        return super().invoke(context, event)


classes = (
    XRAY_OT_import_level,
    exp.ops.XRAY_OT_export_level
)


def register():
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
