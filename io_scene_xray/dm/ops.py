# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import contexts
from .. import icons
from .. import log
from .. import utils
from .. import ie_props
from .. import version_utils


class ImportDmContext(contexts.ImportMeshContext):
    def __init__(self):
        super().__init__()


class ExportDmContext(contexts.ExportMeshContext):
    def __init__(self):
        super().__init__()


filename_ext = '.dm'
op_text = 'Detail Model'


op_import_dm_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.dm', options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE'}
    ),
    'filepath': bpy.props.StringProperty(
        subtype="FILE_PATH", options={'SKIP_SAVE'}
    ),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement, options={'SKIP_SAVE', 'HIDDEN'}
    )
}


class XRAY_OT_import_dm(
        ie_props.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.dm'
    bl_label = 'Import .dm'
    bl_description = 'Imports X-Ray Detail Models (.dm)'
    bl_options = {'REGISTER', 'UNDO'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_import_dm_props.items():
            exec('{0} = op_import_dm_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        textures_folder = version_utils.get_preferences().textures_folder_auto

        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')

        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}

        import_context = ImportDmContext()
        import_context.textures_folder=textures_folder
        import_context.operator=self

        for file in self.files:
            file_ext = os.path.splitext(file.name)[-1].lower()
            if file_ext == filename_ext:
                try:
                    imp.import_file(
                        os.path.join(self.directory, file.name),
                        import_context
                    )
                except utils.AppError as err:
                    import_context.errors.append(err)
            else:
                self.report(
                    {'ERROR'},
                    'Format of {} not recognised'.format(file)
                )
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}


op_export_dms_props = {
    'detail_models': bpy.props.StringProperty(options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype="FILE_PATH"),
    'texture_name_from_image_path': ie_props.PropObjectTextureNamesFromPath()
}


class XRAY_OT_export_dm(ie_props.BaseOperator):
    bl_idname = 'xray_export.dm'
    bl_label = 'Export .dm'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_dms_props.items():
            exec('{0} = op_export_dms_props.get("{0}")'.format(prop_name))

    def draw(self, context):
        self.layout.prop(self, 'texture_name_from_image_path')

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        active_object, selected_objects = utils.get_selection_state(context)
        export_context = ExportDmContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.unique_errors = set()
        for name in self.detail_models.split(','):
            detail_model = context.scene.objects[name]
            if not name.lower().endswith(filename_ext):
                name += filename_ext
            path = self.directory
            try:
                exp.export_file(
                    detail_model,
                    os.path.join(path, name),
                    export_context
                )
            except utils.AppError as err:
                export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        utils.set_selection_state(active_object, selected_objects)
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = version_utils.get_preferences()
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
                bpy.ops.xray_export.dm_file('INVOKE_DEFAULT')
        else:
            self.detail_models = ','.join(
                [obj.name for obj in objs if obj.type == 'MESH']
            )
            context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


op_export_dm_props = {
    'detail_model': bpy.props.StringProperty(options={'HIDDEN'}),
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
    ),
    'texture_name_from_image_path': ie_props.PropObjectTextureNamesFromPath()
}


class XRAY_OT_export_dm_file(
        ie_props.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.dm_file'
    bl_label = 'Export .dm'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_dm_props.items():
            exec('{0} = op_export_dm_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        try:
            self.exp(context.scene.objects[self.detail_model], context)
        except utils.AppError as err:
            log.err(err)
        return {'FINISHED'}

    def draw(self, context):
        self.layout.prop(self, 'texture_name_from_image_path')

    def exp(self, bpy_obj, context):
        active_object, selected_objects = utils.get_selection_state(context)
        export_context = ExportDmContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.unique_errors = set()
        exp.export_file(bpy_obj, self.filepath, export_context)
        utils.set_selection_state(active_object, selected_objects)

    def invoke(self, context, event):
        prefs = version_utils.get_preferences()
        self.texture_name_from_image_path = prefs.dm_texture_names_from_path
        objs = context.selected_objects

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
        self.filepath = self.detail_model

        return super().invoke(context, event)


classes = (
    (XRAY_OT_import_dm, op_import_dm_props),
    (XRAY_OT_export_dm, op_export_dms_props),
    (XRAY_OT_export_dm_file, op_export_dm_props)
)


def register():
    for operator, props in classes:
        version_utils.assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
