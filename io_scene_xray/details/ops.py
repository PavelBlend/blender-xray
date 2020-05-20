import os

import bpy
import bpy_extras

from .. import plugin, plugin_prefs, utils
from ..obj.imp.utils import ImportContext
from .model import imp as model_imp
from .model import exp as model_exp
from . import imp, exp
from ..version_utils import get_import_export_menus, assign_props, IS_28


op_import_dm_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.dm;*.details', options={'HIDDEN'}
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
    'details_models_in_a_row': bpy.props.BoolProperty(
        name='Details Models in a Row', default=True
    ),
    'load_slots': bpy.props.BoolProperty(name='Load Slots', default=True),
    'format': bpy.props.EnumProperty(
        name='Details Format',
        items=(
            ('builds_1096-1230', 'Builds 1096-1230', ''),
            ('builds_1233-1558', 'Builds 1233-1558', '')
        )
    )
}


class OpImportDM(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):

    bl_idname = 'xray_import.dm'
    bl_label = 'Import .dm/.details'
    bl_description = 'Imports X-Ray Detail Model (.dm, .details)'
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}

    if not IS_28:
        for prop_name, prop_value in op_import_dm_props.items():
            exec('{0} = op_import_dm_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):

        textures_folder = plugin_prefs.get_preferences().textures_folder_auto

        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')

        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}

        import_context = ImportContext(
            textures=textures_folder,
            soc_sgroups=None,
            import_motions=None,
            split_by_materials=None,
            operator=self,
            use_motion_prefix_name=False
            )

        import_context.format = self.format
        import_context.details_models_in_a_row = self.details_models_in_a_row
        import_context.load_slots = self.load_slots
        import_context.report = self.report

        try:
            for file in self.files:
                ext = os.path.splitext(file.name)[-1].lower()

                if ext == '.dm':
                    model_imp.import_file(
                        os.path.join(self.directory, file.name),
                        import_context
                        )

                elif ext == '.details':
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

    def draw(self, context):

        layout = self.layout
        row = layout.row()
        row.enabled = False
        row.label(text='%d items' % len(self.files))

        box = layout.box()
        box.label(text='Level Details Options:')

        box.prop(self, 'details_models_in_a_row')
        box.prop(self, 'load_slots')

        if self.load_slots:
            box.label(text='Format:')
            row = box.row()
            row.prop(self, 'format', expand=True)

    def invoke(self, context, event):
        return super().invoke(context, event)


op_export_dms_props = {
    'detail_models': bpy.props.StringProperty(options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype="FILE_PATH"),
    'texture_name_from_image_path': plugin_prefs.PropObjectTextureNamesFromPath()
}

class OpExportDMs(bpy.types.Operator):
    bl_idname = 'xray_export.dms'
    bl_label = 'Export .dm'

    if not IS_28:
        for prop_name, prop_value in op_export_dms_props.items():
            exec('{0} = op_export_dms_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):
        try:
            for name in self.detail_models.split(','):
                detail_model = context.scene.objects[name]
                if not name.lower().endswith('.dm'):
                    name += '.dm'
                path = self.directory

                export_context = plugin.mk_export_context(
                    self.texture_name_from_image_path
                    )

                model_exp.export_file(
                    detail_model, os.path.join(path, name), export_context
                )

        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):

        prefs = plugin_prefs.get_preferences()

        self.texture_name_from_image_path = \
            prefs.object_texture_names_from_path

        objs = context.selected_objects

        if not objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}

        if len(objs) == 1:
            if objs[0].type != 'MESH':
                self.report({'ERROR'}, 'The select object is not a mesh')
                return {'CANCELLED'}
            else:
                bpy.ops.xray_export.dm('INVOKE_DEFAULT')
        else:
            self.detail_models = ','.join(
                [o.name for o in objs if o.type == 'MESH']
            )
            context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


filename_ext = '.dm'
op_export_dm_props = {
    'detail_model': bpy.props.StringProperty(options={'HIDDEN'}),
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
        ),
    'texture_name_from_image_path': plugin_prefs.PropObjectTextureNamesFromPath()
}


class OpExportDM(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = 'xray_export.dm'
    bl_label = 'Export .dm'

    filename_ext = '.dm'

    if not IS_28:
        for prop_name, prop_value in op_export_dm_props.items():
            exec('{0} = op_export_dm_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):
        try:
            self.exp(context.scene.objects[self.detail_model], context)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        return {'FINISHED'}

    def exp(self, bpy_obj, context):
        export_context = plugin.mk_export_context(
            self.texture_name_from_image_path
            )

        model_exp.export_file(bpy_obj, self.filepath, export_context)

    def invoke(self, context, event):

        prefs = plugin_prefs.get_preferences()

        self.texture_name_from_image_path = \
            prefs.object_texture_names_from_path

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


filename_ext = '.details'
op_export_level_details_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
        ),

    'texture_name_from_image_path': \
        plugin_prefs.PropObjectTextureNamesFromPath(),

    'format_version': bpy.props.EnumProperty(
        name='Format',
        items=(
            ('builds_1569-cop', 'Builds 1569-CoP', ''),
            ('builds_1233-1558', 'Builds 1233-1558', ''),
            ('builds_1096-1230', 'Builds 1096-1230', '')
        ),
        default='builds_1569-cop'
    )
}


class OpExportLevelDetails(
    bpy.types.Operator, bpy_extras.io_utils.ExportHelper
    ):

    bl_idname = 'xray_export.details'
    bl_label = 'Export .details'
    bl_options = {'PRESET'}

    filename_ext = '.details'

    if not IS_28:
        for prop_name, prop_value in op_export_level_details_props.items():
            exec('{0} = op_export_level_details_props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'texture_name_from_image_path')
        layout.label(text='Format:')
        col = layout.column()
        col.prop(self, 'format_version', expand=True)

    @utils.execute_with_logger
    @utils.set_cursor_state
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
            self.exp(objs[0], context)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        return {'FINISHED'}

    def exp(self, bpy_obj, context):
        export_context = plugin.mk_export_context(
            self.texture_name_from_image_path
            )

        export_context.level_details_format_version = self.format_version
        exp.export_file(bpy_obj, self.filepath, export_context)

    def invoke(self, context, event):

        prefs = plugin_prefs.get_preferences()

        self.texture_name_from_image_path = \
            prefs.object_texture_names_from_path

        return super().invoke(context, event)


class PackDetailsImages(bpy.types.Operator):
    bl_idname = 'io_scene_xray.pack_details_images'
    bl_label = 'Pack Details Images'
    bl_description = 'Pack Details Images as PNG'

    @classmethod
    def poll(cls, context):
        if context.object:
            if context.object.type == 'EMPTY':
                return True
        return False

    @utils.set_cursor_state
    def execute(self, context):
        slots = context.object.xray.detail.slots
        lighting = slots.ligthing
        meshes = slots.meshes
        images = bpy.data.images

        lights_image = images.get(lighting.lights_image)
        hemi_image = images.get(lighting.hemi_image)
        shadows_image = images.get(lighting.shadows_image)

        mesh_0_image = images.get(meshes.mesh_0)
        mesh_1_image = images.get(meshes.mesh_1)
        mesh_2_image = images.get(meshes.mesh_2)
        mesh_3_image = images.get(meshes.mesh_3)

        slots_images = [lights_image, hemi_image, shadows_image, mesh_0_image,
            mesh_1_image, mesh_2_image, mesh_3_image]

        for image in slots_images:
            if image:
                if IS_28:
                    image.pack()
                else:
                    image.pack(as_png=True)

        return {'FINISHED'}


assign_props([
    (op_import_dm_props, OpImportDM),
    (op_export_dms_props, OpExportDMs),
    (op_export_dm_props, OpExportDM),
    (op_export_level_details_props, OpExportLevelDetails)
])


def menu_func_import(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        OpImportDM.bl_idname, text='X-Ray details (.dm, .details)',
        icon_value=icon
        )


def menu_func_export(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        OpExportDMs.bl_idname, text='X-Ray detail model (.dm)', icon_value=icon)
    self.layout.operator(
        OpExportLevelDetails.bl_idname, text='X-Ray level details (.details)',
        icon_value=icon
        )


def register_operators():
    bpy.utils.register_class(OpImportDM)
    bpy.utils.register_class(OpExportDM)
    bpy.utils.register_class(OpExportDMs)
    bpy.utils.register_class(OpExportLevelDetails)
    bpy.utils.register_class(PackDetailsImages)


def unregister_operators():
    import_menu, export_menu = get_import_export_menus()
    bpy.utils.unregister_class(PackDetailsImages)
    export_menu.remove(menu_func_export)
    import_menu.remove(menu_func_import)
    bpy.utils.unregister_class(OpExportLevelDetails)
    bpy.utils.unregister_class(OpExportDMs)
    bpy.utils.unregister_class(OpExportDM)
    bpy.utils.unregister_class(OpImportDM)
