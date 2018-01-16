
import bpy
from bpy_extras import io_utils
from .. import plugin
from .. import plugin_prefs
from ..utils import AppError


class OpImportDM(bpy.types.Operator, io_utils.ImportHelper):

    bl_idname = 'xray_import.dm'
    bl_label = 'Import .dm/.details'
    bl_description = 'Imports X-Ray Detail Model (.dm, .details)'
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}

    filter_glob = bpy.props.StringProperty(
        default='*.dm;*.details', options={'HIDDEN'}
        )

    directory = bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE'}
        )

    filepath = bpy.props.StringProperty(
        subtype="FILE_PATH", options={'SKIP_SAVE'}
        )

    files = bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement, options={'SKIP_SAVE'}
        )

    details_models_in_a_row = bpy.props.BoolProperty(
        name='Details Models in a Row', default=True
        )

    load_slots = bpy.props.BoolProperty(name='Load Slots', default=True)

    format = bpy.props.EnumProperty(
        name='Details Format',
        items=(
            ('builds_1096-1230', 'Builds 1096-1230', ''),
            ('builds_1233-1558', 'Builds 1233-1558', '')
            )
        )

    def execute(self, context):

        textures_folder = plugin_prefs.get_preferences().get_textures_folder()

        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')

        if len(self.files) == 0:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}

        from . import model
        from . import imp
        from ..fmt_object_imp import ImportContext

        cx = ImportContext(
            report=self.report,
            textures=textures_folder,
            soc_sgroups=None,
            import_motions=None,
            split_by_materials=None,
            op=self,
            bpy=bpy
            )

        cx.format = self.format
        cx.details_models_in_a_row = self.details_models_in_a_row
        cx.load_slots = self.load_slots

        import os

        try:
            for file in self.files:
                ext = os.path.splitext(file.name)[-1].lower()

                if ext == '.dm':
                    model.imp.import_file(
                        os.path.join(self.directory, file.name),
                        cx
                        )

                elif ext == '.details':
                    imp.import_file(
                        os.path.join(self.directory, file.name),
                        cx
                        )

                else:
                    self.report(
                        {'ERROR'},
                        'Format of {} not recognised'.format(file)
                        )

        except AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        return {'FINISHED'}

    def draw(self, context):

        layout = self.layout
        row = layout.row()
        row.enabled = False
        row.label('%d items' % len(self.files))

        box = layout.box()
        box.label('Level Details Options:')

        box.prop(self, 'details_models_in_a_row')
        box.prop(self, 'load_slots')

        if self.load_slots:
            box.label('Format:')
            row = box.row()
            row.prop(self, 'format', expand=True)

    def invoke(self, context, event):
        return super().invoke(context, event)


class OpExportDM(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = 'xray_export.dm'
    bl_label = 'Export .dm'

    filename_ext = '.dm'

    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
        )

    texture_name_from_image_path = \
        plugin_prefs.PropObjectTextureNamesFromPath()

    def execute(self, context):

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

        try:
            self.export(objs[0], context)
        except AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        return {'FINISHED'}

    def export(self, bpy_obj, context):

        from .model.exp import export_file

        cx = plugin._mk_export_context(
            context, self.report, self.texture_name_from_image_path
            )

        export_file(bpy_obj, self.filepath, cx)


    def invoke(self, context, event):

        prefs = plugin_prefs.get_preferences()

        self.texture_name_from_image_path = \
            prefs.object_texture_names_from_path

        return super().invoke(context, event)


class OpExportLevelDetails(bpy.types.Operator, io_utils.ExportHelper):

    bl_idname = 'xray_export.details'
    bl_label = 'Export .details'

    filename_ext = '.details'

    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
        )

    texture_name_from_image_path = \
        plugin_prefs.PropObjectTextureNamesFromPath()

    format_version = bpy.props.EnumProperty(
        name='Format',
        items=(
            ('builds_1569-cop', 'Builds 1569-CoP', ''),
            ('builds_1233-1558', 'Builds 1233-1558', ''),
            ('builds_1096-1230', 'Builds 1096-1230', '')
            ),
        default='builds_1569-cop'
        )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'texture_name_from_image_path')
        layout.label('Format:')
        col = layout.column()
        col.prop(self, 'format_version', expand=True)

    def execute(self, context):

        objs = context.selected_objects

        if not objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}

        if len(objs) > 1:
            self.report({'ERROR'}, 'Too many selected objects found')
            return {'CANCELLED'}

        if objs[0].type != 'EMPTY':
            self.report({'ERROR'}, 'The selected object is not a empty')
            return {'CANCELLED'}

        try:
            self.export(objs[0], context)
        except AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        return {'FINISHED'}

    def export(self, bpy_obj, context):

        from .exp import export_file

        cx = plugin._mk_export_context(
            context, self.report, self.texture_name_from_image_path
            )

        cx.bpy = bpy
        cx.level_details_format_version = self.format_version
        export_file(bpy_obj, self.filepath, cx)

    def invoke(self, context, event):

        prefs = plugin_prefs.get_preferences()

        self.texture_name_from_image_path = \
            prefs.object_texture_names_from_path

        return super().invoke(context, event)


def menu_func_import(self, context):
    self.layout.operator(
        OpImportDM.bl_idname, text='X-Ray details (.dm, .details)'
        )


def menu_func_export(self, context):
    self.layout.operator(OpExportDM.bl_idname, text='X-Ray detail model (.dm)')
    self.layout.operator(
        OpExportLevelDetails.bl_idname, text='X-Ray level details (.details)'
        )


def register_operators():
    bpy.utils.register_class(OpImportDM)
    bpy.utils.register_class(OpExportDM)
    bpy.utils.register_class(OpExportLevelDetails)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister_operators():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(OpExportLevelDetails)
    bpy.utils.unregister_class(OpExportDM)
    bpy.utils.unregister_class(OpImportDM)
