# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import ie
from .. import contexts
from ... import log
from ... import utils


class ImportOgfContext(
        contexts.ImportMeshContext,
        contexts.ImportAnimationContext
    ):
    def __init__(self):
        super().__init__()
        self.meshes_folder = None
        self.import_bone_parts = None


class ExportOgfContext(
        contexts.ExportMeshContext,
        contexts.ExportAnimationContext
    ):
    def __init__(self):
        super().__init__()
        self.fmt_ver = None
        self.hq_export = None


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
    'import_motions': ie.PropObjectMotionsImport()
}


class XRAY_OT_import_ogf(
        ie.BaseOperator,
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

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        prefs = utils.version.get_preferences()
        textures_folder = prefs.textures_folder_auto
        meshes_folder = prefs.meshes_folder_auto
        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')
        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}
        import_context = ImportOgfContext()
        import_context.textures_folder = textures_folder
        import_context.meshes_folder = meshes_folder
        import_context.import_motions = self.import_motions
        import_context.import_bone_parts = True
        import_context.add_actions_to_motion_list = True
        for file in self.files:
            file_path = os.path.join(self.directory, file.name)
            try:
                imp.main.import_file(import_context, file_path, file.name)
            except log.AppError as err:
                import_context.errors.append(err)
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        utils.draw.draw_files_count(self)
        layout.prop(self, 'import_motions')

    def invoke(self, context, event):
        preferences = utils.version.get_preferences()
        self.import_motions = preferences.ogf_import_motions
        return super().invoke(context, event)


export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'texture_name_from_image_path': ie.PropObjectTextureNamesFromPath(),
    'fmt_version': ie.PropSDKVersion(),
    'hq_export': ie.prop_omf_high_quality(),
    'export_motions': ie.PropObjectMotionsExport()
}


class XRAY_OT_export_ogf_file(
        ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.ogf_file'
    bl_label = 'Export .ogf'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        utils.draw.draw_fmt_ver_prop(layout, self, 'fmt_version')
        layout.prop(self, 'export_motions')
        row = layout.row()
        row.active = self.fmt_version == 'cscop' and self.export_motions
        row.prop(self, 'hq_export', text='High Quatily Motions')
        layout.prop(self, 'texture_name_from_image_path')

    @log.execute_with_logger
    @utils.execute_require_filepath
    @utils.ie.set_initial_state
    def execute(self, context):
        export_context = ExportOgfContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.fmt_ver = self.fmt_version
        export_context.hq_export = self.hq_export
        export_context.export_motions = self.export_motions
        try:
            exp.export_file(self.exported_object, self.filepath, export_context)
        except log.AppError as err:
            export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        for obj in self.selected_objects:
            utils.version.select_object(obj)
        utils.version.set_active_object(self.exported_object)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = utils.version.get_preferences()
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
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'texture_name_from_image_path': ie.PropObjectTextureNamesFromPath(),
    'export_motions': ie.PropObjectMotionsExport()
}


class XRAY_OT_export_ogf(ie.BaseOperator):
    bl_idname = 'xray_export.ogf'
    bl_label = 'Export .ogf'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = batch_export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'export_motions')
        layout.prop(self, 'texture_name_from_image_path')

    @log.execute_with_logger
    @utils.ie.set_initial_state
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
            except log.AppError as err:
                export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = utils.version.get_preferences()
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
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
