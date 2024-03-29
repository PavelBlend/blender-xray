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


class ImportDmContext(contexts.ImportMeshContext):
    pass


class ExportDmContext(contexts.ExportMeshContext):
    pass


filename_ext = '.dm'
op_text = 'Detail Model'


class XRAY_OT_import_dm(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.dm'
    bl_label = 'Import .dm'
    bl_description = 'Imports X-Ray Detail Models (.dm)'
    bl_options = {'REGISTER', 'UNDO'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )
    directory = bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'HIDDEN'}
    )
    filepath = bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE', 'HIDDEN'}
    )
    files = bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'SKIP_SAVE', 'HIDDEN'}
    )
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'meshes_folder')

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Import *.dm')

        # check selected files
        has_sel = utils.ie.has_selected_files(self)
        if not has_sel:
            return {'CANCELLED'}

        import_context = ImportDmContext()
        import_context.operator = self

        utils.ie.import_files(
            self.directory,
            self.files,
            imp.import_file,
            import_context
        )

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        return super().invoke(context, event)


class XRAY_OT_export_dm(utils.ie.BaseOperator):
    bl_idname = 'xray_export.dm'
    bl_label = 'Export .dm'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )
    detail_models = bpy.props.StringProperty(options={'HIDDEN'})
    directory = bpy.props.StringProperty(subtype='FILE_PATH')
    texture_name_from_image_path = ie.PropObjectTextureNamesFromPath()
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'meshes_folder')
        self.layout.prop(self, 'texture_name_from_image_path')

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.dm')

        export_context = ExportDmContext()
        export_context.operator = self
        export_context.texname_from_path = self.texture_name_from_image_path

        for name in self.detail_models.split(','):
            detail_model = context.scene.objects[name]
            name = utils.ie.add_file_ext(name, filename_ext)
            path = self.directory
            try:
                exp.export_file(
                    detail_model,
                    os.path.join(path, name),
                    export_context
                )
            except log.AppError as err:
                export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        prefs = utils.version.get_preferences()
        self.texture_name_from_image_path = prefs.dm_texture_names_from_path
        objs = context.selected_objects

        if not objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}

        if len(objs) == 1:
            if objs[0].type != 'MESH':
                self.report({'ERROR'}, 'The select object is not mesh')
                return {'CANCELLED'}
            else:
                return bpy.ops.xray_export.dm_file('INVOKE_DEFAULT')
        else:
            object_list = [obj.name for obj in objs if obj.type == 'MESH']
            if not object_list:
                self.report(
                    {'ERROR'},
                    'There are no meshes among the selected objects'
                )
                return {'CANCELLED'}
            if len(object_list) == 1:
                return bpy.ops.xray_export.dm_file('INVOKE_DEFAULT')
            self.detail_models = ','.join(object_list)
            context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class XRAY_OT_export_dm_file(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.dm_file'
    bl_label = 'Export .dm'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = filename_ext

    detail_model = bpy.props.StringProperty(options={'HIDDEN'})
    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )
    texture_name_from_image_path = ie.PropObjectTextureNamesFromPath()

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.dm')

        try:
            self.exp(context.scene.objects[self.detail_model], context)
        except log.AppError as err:
            log.err(err)

        return {'FINISHED'}

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'meshes_folder')
        self.layout.prop(self, 'texture_name_from_image_path')

    def exp(self, bpy_obj, context):
        export_context = ExportDmContext()
        export_context.operator = self
        export_context.texname_from_path = self.texture_name_from_image_path
        exp.export_file(bpy_obj, self.filepath, export_context)

    def invoke(self, context, event):    # pragma: no cover
        prefs = utils.version.get_preferences()
        self.texture_name_from_image_path = prefs.dm_texture_names_from_path
        objs = [
            obj
            for obj in context.selected_objects
                if obj.type == 'MESH'
        ]

        if not objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}

        if len(objs) > 1:
            self.report({'ERROR'}, 'Too many selected objects found')
            return {'CANCELLED'}

        if objs[0].type != 'MESH':
            self.report({'ERROR'}, 'The selected object is not mesh')
            return {'CANCELLED'}

        self.detail_model = objs[0].name
        self.filepath = utils.ie.add_file_ext(self.detail_model, filename_ext)

        return super().invoke(context, event)


classes = (
    XRAY_OT_import_dm,
    XRAY_OT_export_dm,
    XRAY_OT_export_dm_file
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
