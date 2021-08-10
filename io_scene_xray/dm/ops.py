import os

import bpy
import bpy_extras

from .. import ui, utils, context
from ..obj.exp import props as obj_exp_props
from ..version_utils import (
    get_import_export_menus, assign_props, IS_28, get_preferences
)
from . import imp
from . import exp


class ImportDmContext(context.ImportMeshContext):
    def __init__(self):
        context.ImportMeshContext.__init__(self)


class ExportDmContext(context.ExportMeshContext):
    def __init__(self):
        context.ExportMeshContext.__init__(self)


filename_ext = '.dm'


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
        type=bpy.types.OperatorFileListElement, options={'SKIP_SAVE'}
    )
}


class XRAY_OT_import_dm(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'xray_import.dm'
    bl_label = 'Import .dm'
    bl_description = 'Imports X-Ray Detail Models (.dm)'
    bl_options = {'REGISTER', 'UNDO'}

    if not IS_28:
        for prop_name, prop_value in op_import_dm_props.items():
            exec('{0} = op_import_dm_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):

        textures_folder = get_preferences().textures_folder_auto

        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')

        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}

        import_context = ImportDmContext()
        import_context.textures_folder=textures_folder
        import_context.operator=self

        try:
            for file in self.files:
                ext = os.path.splitext(file.name)[-1].lower()

                if ext == filename_ext:
                    imp.import_file(
                        os.path.join(self.directory, file.name),
                        import_context
                    )

                else:
                    self.report(
                        {'ERROR'},
                        'Format of {} not recognised'.format(file)
                        )

        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        return {'FINISHED'}


op_export_dms_props = {
    'detail_models': bpy.props.StringProperty(options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype="FILE_PATH"),
    'texture_name_from_image_path': obj_exp_props.PropObjectTextureNamesFromPath()
}

class XRAY_OT_export_dm(bpy.types.Operator):
    bl_idname = 'xray_export.dm'
    bl_label = 'Export .dm'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    if not IS_28:
        for prop_name, prop_value in op_export_dms_props.items():
            exec('{0} = op_export_dms_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        try:
            for name in self.detail_models.split(','):
                detail_model = context.scene.objects[name]
                if not name.lower().endswith(filename_ext):
                    name += filename_ext
                path = self.directory

                export_context = ExportDmContext()
                export_context.texname_from_path = self.texture_name_from_image_path

                model_exp.export_file(
                    detail_model, os.path.join(path, name), export_context
                )

        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):

        preferences = get_preferences()

        self.texture_name_from_image_path = \
            preferences.dm_texture_names_from_path

        objs = context.selected_objects

        if not objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}

        if len(objs) == 1:
            if objs[0].type != 'MESH':
                self.report({'ERROR'}, 'The select object is not a mesh')
                return {'CANCELLED'}
            else:
                bpy.ops.xray_export.dm_file('INVOKE_DEFAULT')
        else:
            self.detail_models = ','.join(
                [o.name for o in objs if o.type == 'MESH']
            )
            context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


op_export_dm_props = {
    'detail_model': bpy.props.StringProperty(options={'HIDDEN'}),
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
        ),
    'texture_name_from_image_path': obj_exp_props.PropObjectTextureNamesFromPath()
}


class XRAY_OT_export_single_dm(
        bpy.types.Operator,
        bpy_extras.io_utils.ExportHelper
    ):

    bl_idname = 'xray_export.dm_file'
    bl_label = 'Export .dm'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = filename_ext

    if not IS_28:
        for prop_name, prop_value in op_export_dm_props.items():
            exec('{0} = op_export_dm_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        try:
            self.exp(context.scene.objects[self.detail_model], context)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        return {'FINISHED'}

    def exp(self, bpy_obj, context):
        export_context = ExportDmContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        exp.export_file(bpy_obj, self.filepath, export_context)

    def invoke(self, context, event):

        preferences = get_preferences()

        self.texture_name_from_image_path = \
            preferences.dm_texture_names_from_path

        objs = context.selected_objects

        if not objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}

        if len(objs) > 1:
            self.report({'ERROR'}, 'Too many selected objects found')
            return {'CANCELLED'}

        if objs[0].type != 'MESH':
            self.report({'ERROR'}, 'The selected object is not a mesh')
            return {'CANCELLED'}

        self.detail_model = objs[0].name
        self.filepath = self.detail_model

        return super().invoke(context, event)


def menu_func_import(self, context):
    icon = ui.icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_import_dm.bl_idname, text='X-Ray detail model (.dm)',
        icon_value=icon
    )


def menu_func_export(self, context):
    icon = ui.icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_dm.bl_idname,
        text='X-Ray detail model (.dm)',
        icon_value=icon
    )


classes = (
    (XRAY_OT_import_dm, op_import_dm_props),
    (XRAY_OT_export_dm, op_export_dms_props),
    (XRAY_OT_export_single_dm, op_export_dm_props)
)


def register():
    for operator, props in classes:
        assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    import_menu, export_menu = get_import_export_menus()
    export_menu.remove(menu_func_export)
    import_menu.remove(menu_func_import)
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
