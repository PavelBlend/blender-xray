import bpy
from bpy_extras import io_utils

from ..utils import (
    execute_with_logger, execute_require_filepath, mk_export_context
)
from .. import registry, plugin_prefs
from . import exp


class ModelExportHelper:
    selection_only = bpy.props.BoolProperty(
        name='Selection Only',
        description='Export only selected objects'
    )

    def export(self, bpy_obj, context):
        pass

    @execute_with_logger
    @execute_require_filepath
    def execute(self, context):
        objs = context.selected_objects if self.selection_only else context.scene.objects
        roots = [obj for obj in objs if obj.xray.isroot]
        if not roots:
            self.report({'ERROR'}, 'Cannot find object root')
            return {'CANCELLED'}
        if len(roots) > 1:
            self.report({'ERROR'}, 'Too many object roots found')
            return {'CANCELLED'}
        return self.export(roots[0], context)


@registry.module_thing
class OpExportOgf(bpy.types.Operator, io_utils.ExportHelper, ModelExportHelper):
    bl_idname = 'xray_export.ogf'
    bl_label = 'Export .ogf'

    filename_ext = '.ogf'
    filter_glob = bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'})

    texture_name_from_image_path = plugin_prefs.PropObjectTextureNamesFromPath()

    def export(self, bpy_obj, context):
        export_context = mk_export_context(self.texture_name_from_image_path)
        exp.export_file(bpy_obj, self.filepath, export_context)
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
        self.texture_name_from_image_path = prefs.object_texture_names_from_path
        return super().invoke(context, event)
