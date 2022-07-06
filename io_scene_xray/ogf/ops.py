# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import icons
from .. import log
from .. import contexts
from .. import version_utils
from .. import ie_props
from .. import draw_utils
from .. import utils


class ImportOgfContext(
        contexts.ImportMeshContext,
        contexts.ImportAnimationContext
    ):
    def __init__(self):
        super().__init__()
        self.import_bone_parts = None


class ExportOgfContext(
        contexts.ExportMeshContext,
        contexts.ExportAnimationContext
    ):
    def __init__(self):
        super().__init__()


op_text = 'Game Object'
filename_ext = '.ogf'

import_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.ogf', options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE'}
    ),
    'filepath': bpy.props.StringProperty(
        subtype="FILE_PATH", options={'SKIP_SAVE'}
    ),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement, options={'SKIP_SAVE'}
    ),
    'import_motions': ie_props.PropObjectMotionsImport()
}


class XRAY_OT_import_ogf(
        ie_props.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.ogf'
    bl_label = 'Import .ogf'
    bl_description = 'Import X-Ray Compiled Game Model (.ogf)'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

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
        prefs = version_utils.get_preferences()
        textures_folder = prefs.textures_folder_auto
        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')
        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}
        import_context = ImportOgfContext()
        import_context.textures_folder = textures_folder
        import_context.import_motions = self.import_motions
        import_context.import_bone_parts = True
        import_context.add_actions_to_motion_list = True
        for file in self.files:
            file_path = os.path.join(self.directory, file.name)
            try:
                imp.import_file(import_context, file_path, file.name)
            except utils.AppError as err:
                import_context.errors.append(err)
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        draw_utils.draw_files_count(self)
        layout.prop(self, 'import_motions')

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.import_motions = preferences.ogf_import_motions
        return super().invoke(context, event)


export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'texture_name_from_image_path': ie_props.PropObjectTextureNamesFromPath(),
    'export_motions': ie_props.PropObjectMotionsExport()
}


class XRAY_OT_export_ogf_file(
        ie_props.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.ogf_file'
    bl_label = 'Export .ogf'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.execute_require_filepath
    @utils.set_cursor_state
    def execute(self, context):
        export_context = ExportOgfContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.export_motions = self.export_motions
        try:
            exp.export_file(self.exported_object, self.filepath, export_context)
        except utils.AppError as err:
            export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        for obj in self.selected_objects:
            version_utils.select_object(obj)
        version_utils.set_active_object(self.exported_object)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.texture_name_from_image_path = preferences.ogf_texture_names_from_path
        self.export_motions = preferences.ogf_export_motions
        self.filepath = context.object.name
        objs = context.selected_objects
        self.selected_objects = context.selected_objects
        roots = [obj for obj in objs if obj.xray.isroot]
        if not roots:
            self.report({'ERROR'}, 'Cannot find object root')
            return {'CANCELLED'}
        if len(roots) > 1:
            self.report({'ERROR'}, 'Too many object roots found')
            return {'CANCELLED'}
        self.exported_object = roots[0]
        return super().invoke(context, event)


batch_export_props = {
    'directory': bpy.props.StringProperty(
        subtype="FILE_PATH",
        options={'HIDDEN'}
    ),
    'texture_name_from_image_path': ie_props.PropObjectTextureNamesFromPath(),
    'export_motions': ie_props.PropObjectMotionsExport()
}


class XRAY_OT_export_ogf(ie_props.BaseOperator):
    bl_idname = 'xray_export.ogf'
    bl_label = 'Export .ogf'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = batch_export_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        export_context = ExportOgfContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.export_motions = self.export_motions
        for obj in self.roots:
            file_name = obj.name
            if not file_name.endswith(filename_ext):
                file_name += filename_ext
            file_path = os.path.join(self.directory, file_name)
            try:
                exp.export_file(obj, file_path, export_context)
            except utils.AppError as err:
                export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.texture_name_from_image_path = preferences.ogf_texture_names_from_path
        self.export_motions = preferences.ogf_export_motions
        self.selected_objects = context.selected_objects
        self.roots = [obj for obj in self.selected_objects if obj.xray.isroot]
        if not self.roots:
            self.report({'ERROR'}, 'Cannot find root-objects')
            return {'CANCELLED'}
        if len(self.roots) == 1:
            return bpy.ops.xray_export.ogf_file('INVOKE_DEFAULT')
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_import_ogf,
    XRAY_OT_export_ogf,
    XRAY_OT_export_ogf_file
)


def register():
    version_utils.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
