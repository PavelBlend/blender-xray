# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import utils
from .. import log
from .. import icons
from .. import contexts
from .. import version_utils
from .. import ie_props


class ImportLevelContext(contexts.ImportMeshContext):
    def __init__(self):
        super().__init__()


op_text = 'Game Level'
file_name_text = 'level'


import_props = {
    'filter_glob': bpy.props.StringProperty(
        default='level', options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE', 'HIDDEN'}
    ),
    'filepath': bpy.props.StringProperty(
        subtype="FILE_PATH", options={'SKIP_SAVE', 'HIDDEN'}
    )
}


class XRAY_OT_import_level(
        ie_props.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.level'
    bl_label = 'Import level'
    bl_description = 'Import X-Ray Game Level (level)'
    bl_options = {'REGISTER', 'UNDO'}

    text = op_text
    filename_ext = ''
    ext = file_name_text
    props = import_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        preferences = version_utils.get_preferences()
        textures_folder = preferences.textures_folder_auto
        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')
        if not self.filepath:
            self.report({'ERROR'}, 'No file selected')
            return {'CANCELLED'}
        import_context = ImportLevelContext()
        import_context.textures_folder=textures_folder
        import_context.operator=self
        import_context.filepath = self.filepath
        try:
            imp.import_file(import_context, self)
        except utils.AppError as err:
            import_context.errors.append(err)
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    def invoke(self, context, event):
        return super().invoke(context, event)


export_props = {
    'directory': bpy.props.StringProperty(
        subtype='DIR_PATH', options={'HIDDEN'}
    ),
    'filter_glob': bpy.props.StringProperty(
        default='level;level.geom;level.geomx;level.cform',
        options={'HIDDEN'}
    )
}


class XRAY_OT_export_level(ie_props.BaseOperator):
    bl_idname = 'xray_export.level'
    bl_label = 'Export level'

    text = op_text
    filename_ext = ''
    ext = file_name_text
    props = export_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def export(self, level_object, context):
        exp.export_file(level_object, self.directory)
        return {'FINISHED'}

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        level_object = context.object
        if not level_object.xray.is_level:
            self.report(
                {'ERROR'},
                'Object "{}" does not have level parameter enabled.'.format(
                    level_object.name
                )
            )
            return {'CANCELLED'}
        if level_object.xray.level.object_type != 'LEVEL':
            self.report(
                {'ERROR'},
                'Object "{0}" has an invalid type: {1}. Must be Level.'.format(
                    level_object.name,
                    level_object.xray.level.object_type
                )
            )
            return {'CANCELLED'}
        return self.export(level_object, context)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_import_level,
    XRAY_OT_export_level
)


def register():
    version_utils.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
