import os

import bpy
from bpy_extras import io_utils

from . import props
from .. import plugin, plugin_prefs, prefs
from ..utils import execute_with_logger, FilenameExtHelper, set_cursor_state
from ..version_utils import assign_props, IS_28


op_import_anm_props = {
    'filter_glob': bpy.props.StringProperty(default='*.anm', options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'files': bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement),
    'camera_animation': props.PropAnmCameraAnimation()
}


class OpImportAnm(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = 'xray_import.anm'
    bl_label = 'Import .anm'
    bl_description = 'Imports X-Ray animation'
    bl_options = {'UNDO', 'PRESET'}

    if not IS_28:
        for prop_name, prop_value in op_import_anm_props.items():
            exec('{0} = op_import_anm_props.get("{0}")'.format(prop_name))

    @execute_with_logger
    @set_cursor_state
    def execute(self, _context):
        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        from .imp import import_file, ImportAnmContext
        import_context = ImportAnmContext()
        import_context.camera_animation = self.camera_animation
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            if ext == '.anm':
                import_file(os.path.join(self.directory, file.name), import_context)
            else:
                self.report({'ERROR'}, 'Format of {} not recognised'.format(file))
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = prefs.utils.get_preferences()
        self.camera_animation = preferences.anm_create_camera
        return super().invoke(context, event)


filename_ext = '.anm'
op_export_anm_props = {
    'filter_glob': bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'}),
}


class OpExportAnm(bpy.types.Operator, FilenameExtHelper):
    bl_idname = 'xray_export.anm'
    bl_label = 'Export .anm'
    bl_description = 'Exports X-Ray animation'

    filename_ext = '.anm'

    if not IS_28:
        for prop_name, prop_value in op_export_anm_props.items():
            exec('{0} = op_export_anm_props.get("{0}")'.format(prop_name))

    @set_cursor_state
    def export(self, context):
        from .exp import export_file

        obj = context.active_object
        if not obj.animation_data:
            self.report({'ERROR'}, 'Object \'{}\' has no animation data'.format(obj.name))
            return {'CANCELLED'}
        export_file(obj, self.filepath)


def menu_func_import(self, _context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        OpImportAnm.bl_idname, text='X-Ray animation (.anm)', icon_value=icon
    )


def menu_func_export(self, _context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        OpExportAnm.bl_idname,
        text='X-Ray animation (.anm)',
        icon_value=icon
    )


def register():
    assign_props([
        (op_import_anm_props, OpImportAnm),
        (op_export_anm_props, OpExportAnm)
    ])
    bpy.utils.register_class(OpImportAnm)
    bpy.utils.register_class(OpExportAnm)


def unregister():
    bpy.utils.unregister_class(OpExportAnm)
    bpy.utils.unregister_class(OpImportAnm)
