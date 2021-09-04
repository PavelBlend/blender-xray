# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import icons
from .. import contexts
from .. import version_utils
from .. import plugin_props
from .. import utils


def menu_func_import(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_import_ogf.bl_idname,
        text=utils.build_op_label(XRAY_OT_export_ogf),
        icon_value=icon
    )


def menu_func_export(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_ogf.bl_idname,
        text=utils.build_op_label(XRAY_OT_export_ogf),
        icon_value=icon
    )


class ImportOgfContext(contexts.ImportMeshContext):
    def __init__(self):
        contexts.ImportMeshContext.__init__(self)


class ExportOgfContext(contexts.ExportMeshContext):
    def __init__(self):
        contexts.ExportMeshContext.__init__(self)


op_text = 'Game Object'
filename_ext = '.ogf'

op_import_ogf_props = {
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
    )
}


class XRAY_OT_import_ogf(
        plugin_props.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.ogf'
    bl_label = 'Import .ogf'
    bl_description = 'Import X-Ray Compiled Game Model (.ogf)'
    bl_options = {'REGISTER', 'UNDO'}

    draw_fun = menu_func_import
    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_import_ogf_props.items():
            exec('{0} = op_import_ogf_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        prefs = version_utils.get_preferences()
        textures_folder = prefs.textures_folder_auto
        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')
        if not self.files[0].name:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        import_context = ImportOgfContext()
        import_context.textures_folder = textures_folder
        for file in self.files:
            file_path = os.path.join(self.directory, file.name)
            if not os.path.exists(file_path):
                self.report(
                    {'ERROR'},
                    'File not found: {}'.format(file_path)
                )
            try:
                imp.import_file(import_context, file_path, file.name)
            except utils.AppError as err:
                self.report({'ERROR'}, str(err))
        return {'FINISHED'}


op_export_ogf_props = {
    'filter_glob': bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'}),
    'texture_name_from_image_path': plugin_props.PropObjectTextureNamesFromPath()
}


class XRAY_OT_export_ogf(
        plugin_props.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.ogf'
    bl_label = 'Export .ogf'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    draw_fun = menu_func_export
    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_ogf_props.items():
            exec('{0} = op_export_ogf_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.execute_require_filepath
    @utils.set_cursor_state
    def execute(self, context):
        export_context = ExportOgfContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        exp.export_file(self.exported_object, self.filepath, export_context)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.texture_name_from_image_path = preferences.object_texture_names_from_path
        self.filepath = context.object.name
        objs = context.selected_objects
        roots = [obj for obj in objs if obj.xray.isroot]
        if not roots:
            self.report({'ERROR'}, 'Cannot find object root')
            return {'CANCELLED'}
        if len(roots) > 1:
            self.report({'ERROR'}, 'Too many object roots found')
            return {'CANCELLED'}
        self.exported_object = roots[0]
        return super().invoke(context, event)


classes = (
    (XRAY_OT_import_ogf, op_import_ogf_props),
    (XRAY_OT_export_ogf, op_export_ogf_props)
)


def register():
    for operator, props in classes:
        version_utils.assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
