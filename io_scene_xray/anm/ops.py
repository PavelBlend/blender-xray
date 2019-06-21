import os

import bpy
from bpy_extras import io_utils

from .. import plugin_prefs, registry
from ..utils import execute_with_logger, FilenameExtHelper, AppError, set_cursor_state
from ..version_utils import assign_props


op_import_anm_props = {
    'filter_glob': bpy.props.StringProperty(default='*.anm', options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'files': bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement),
    'camera_animation': plugin_prefs.PropAnmCameraAnimation()
}


@registry.module_thing
class OpImportAnm(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = 'xray_import.anm'
    bl_label = 'Import .anm'
    bl_description = 'Imports X-Ray animation'
    bl_options = {'UNDO'}

    @execute_with_logger
    @set_cursor_state
    def execute(self, _context):
        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        from .imp import import_file, ImportContext
        import_context = ImportContext(
            camera_animation=self.camera_animation
        )
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            if ext == '.anm':
                import_file(os.path.join(self.directory, file.name), import_context)
            else:
                self.report({'ERROR'}, 'Format of {} not recognised'.format(file))
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
        self.camera_animation = prefs.anm_create_camera
        return super().invoke(context, event)


filename_ext = '.anm'
op_export_anm_props = {
    'filter_glob': bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'}),
}


@registry.module_thing
class OpExportAnm(bpy.types.Operator, FilenameExtHelper):
    bl_idname = 'xray_export.anm'
    bl_label = 'Export .anm'
    bl_description = 'Exports X-Ray animation'

    @set_cursor_state
    def export(self, context):
        from .exp import export_file

        obj = context.active_object
        if not obj.animation_data:
            self.report({'ERROR'}, 'Object \'{}\' has no animation data'.format(obj.name))
            return {'CANCELLED'}
        export_file(obj, self.filepath)


assign_props([
    (op_import_anm_props, OpImportAnm),
    (op_export_anm_props, OpExportAnm)
])
