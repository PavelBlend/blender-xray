# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import utils
from .. import icons
from .. import contexts
from .. import version_utils
from .. import plugin_props


class ImportLevelContext(contexts.ImportMeshContext):
    def __init__(self):
        contexts.ImportMeshContext.__init__(self)


op_import_level_props = {
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
        plugin_props.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.level'
    bl_label = 'Import level'
    bl_description = 'Import X-Ray Game Level (level)'
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
        for prop_name, prop_value in op_import_level_props.items():
            exec('{0} = op_import_level_props.get("{0}")'.format(prop_name))

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
        except utils.AppError as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        return super().invoke(context, event)


op_export_level_props = {
    'directory': bpy.props.StringProperty(
        subtype='DIR_PATH', options={'HIDDEN'}
    ),
    'filter_glob': bpy.props.StringProperty(
        default='level;level.geom;level.geomx;level.cform',
        options={'HIDDEN'}
    )
}


class XRAY_OT_export_level(plugin_props.BaseOperator):
    bl_idname = 'xray_export.level'
    bl_label = 'Export level'

    filename_ext = ''

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_level_props.items():
            exec('{0} = op_export_level_props.get("{0}")'.format(prop_name))

    def export(self, level_object, context):
        exp.export_file(level_object, self.directory)
        return {'FINISHED'}

    @utils.set_cursor_state
    @utils.execute_with_logger
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


def menu_func_import(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_import_level.bl_idname,
        text='X-Ray game level (level)',
        icon_value=icon
    )


def menu_func_export(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_level.bl_idname,
        text='X-Ray game level (level)',
        icon_value=icon
    )


def register():
    version_utils.assign_props([
        (op_import_level_props, XRAY_OT_import_level),
        (op_export_level_props, XRAY_OT_export_level)
    ])
    bpy.utils.register_class(XRAY_OT_import_level)
    bpy.utils.register_class(XRAY_OT_export_level)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_export_level)
    bpy.utils.unregister_class(XRAY_OT_import_level)
