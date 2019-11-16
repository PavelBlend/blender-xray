import bpy, bpy_extras

from .. import utils, plugin, plugin_prefs
from ..version_utils import get_import_export_menus, assign_props, IS_28
from ..obj.imp import utils as obj_imp_utils
from . import imp, exp


op_import_level_props = {
    'filter_glob': bpy.props.StringProperty(
        default='level', options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE'}
    ),
    'filepath': bpy.props.StringProperty(
        subtype="FILE_PATH", options={'SKIP_SAVE'}
    )
}


class IMPORT_OT_xray_level(
        bpy.types.Operator, bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.level'
    bl_label = 'Import level'
    bl_description = 'Import X-Ray Game Level (level)'
    bl_options = {'REGISTER', 'UNDO'}

    if not IS_28:
        for prop_name, prop_value in op_import_level_props.items():
            exec('{0} = op_import_level_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):
        textures_folder = plugin_prefs.get_preferences().textures_folder_auto
        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')
        if not self.filepath:
            self.report({'ERROR'}, 'No file selected')
            return {'CANCELLED'}
        import_context = obj_imp_utils.ImportContext(
            textures=textures_folder,
            soc_sgroups=None,
            import_motions=None,
            split_by_materials=None,
            operator=self,
            use_motion_prefix_name=None,
            objects=None
        )
        import_context.file_path = self.filepath
        try:
            imp.import_file(import_context, self)
        except utils.AppError as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        return super().invoke(context, event)


op_export_level_props = {
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'filter_glob': bpy.props.StringProperty(
        default='level;level.geom;level.geomx;level.cform',
        options={'HIDDEN'}
    )
}


class EXPORT_OT_xray_level(bpy.types.Operator):
    bl_idname = 'xray_export.level'
    bl_label = 'Export Level'

    filename_ext = ''

    if not IS_28:
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
            self.report({'ERROR'}, 'Object "{}" does not have level parameter enabled.'.format(level_object.name))
            return {'CANCELLED'}
        if level_object.xray.level.object_type != 'LEVEL':
            self.report({'ERROR'}, 'Object "{0}" has an invalid type: {1}. Must be Level.'.format(
                level_object.name,
                level_object.xray.level.object_type
            ))
            return {'CANCELLED'}
        return self.export(level_object, context)

    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


assign_props([
    (op_import_level_props, IMPORT_OT_xray_level),
    (op_export_level_props, EXPORT_OT_xray_level)
])


def menu_func_import(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        IMPORT_OT_xray_level.bl_idname,
        text='X-Ray game level (level)',
        icon_value=icon
    )


def menu_func_export(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        EXPORT_OT_xray_level.bl_idname,
        text='X-Ray game level (level)',
        icon_value=icon
    )


def register_operators():
    bpy.utils.register_class(IMPORT_OT_xray_level)
    bpy.utils.register_class(EXPORT_OT_xray_level)


def unregister_operators():
    bpy.utils.unregister_class(EXPORT_OT_xray_level)
    bpy.utils.unregister_class(IMPORT_OT_xray_level)
