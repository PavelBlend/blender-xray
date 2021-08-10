import os

import bpy
import bpy_extras

from .. import ui, utils
from .. import context
from ..obj.exp import props as obj_exp_props
from ..dm import imp as model_imp
from ..dm import exp as model_exp
from ..version_utils import (
    get_import_export_menus, assign_props, IS_28, get_preferences
)
from . import imp, exp, props


FORMAT_VERSION_LABEL = 'Format Version:'


class ImportDetailsContext(context.ImportMeshContext):
    def __init__(self):
        context.ImportMeshContext.__init__(self)
        self.format_version = None
        self.details_models_in_a_row = None
        self.load_slots = None


class ExportDetailsContext(context.ExportMeshContext):
    def __init__(self):
        context.ExportMeshContext.__init__(self)
        self.level_details_format_version = None


op_import_details_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.details', options={'HIDDEN'}
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
    'details_models_in_a_row': props.prop_details_models_in_a_row(),
    'load_slots': props.prop_details_load_slots(),
    'details_format': props.prop_details_format()
}


class XRAY_OT_import_details(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):

    bl_idname = 'xray_import.details'
    bl_label = 'Import .details'
    bl_description = 'Imports X-Ray Level Details Models (.details)'
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}

    if not IS_28:
        for prop_name, prop_value in op_import_details_props.items():
            exec('{0} = op_import_details_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):

        textures_folder = get_preferences().textures_folder_auto

        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')

        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}

        import_context = ImportDetailsContext()
        import_context.textures_folder=textures_folder
        import_context.operator=self
        import_context.format_version = self.details_format
        import_context.details_models_in_a_row = self.details_models_in_a_row
        import_context.load_slots = self.load_slots

        try:
            for file in self.files:
                ext = os.path.splitext(file.name)[-1].lower()

                if ext == '.details':
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

        layout.prop(self, 'details_models_in_a_row')
        layout.prop(self, 'load_slots')

        col = layout.column()
        col.active = self.load_slots

        col.label(text=FORMAT_VERSION_LABEL)
        row = col.row()
        row.prop(self, 'details_format', expand=True)

    def invoke(self, context, event):
        preferences = get_preferences()
        self.details_models_in_a_row = preferences.details_models_in_a_row
        self.load_slots = preferences.load_slots
        self.details_format = preferences.details_format
        return super().invoke(context, event)


filename_ext = '.details'
op_export_details_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
        ),

    'texture_name_from_image_path': \
        obj_exp_props.PropObjectTextureNamesFromPath(),

    'format_version': props.prop_details_format_version()
}


class XRAY_OT_export_details(
        bpy.types.Operator, bpy_extras.io_utils.ExportHelper
    ):

    bl_idname = 'xray_export.details'
    bl_label = 'Export .details'
    bl_options = {'PRESET'}

    filename_ext = '.details'

    if not IS_28:
        for prop_name, prop_value in op_export_details_props.items():
            exec('{0} = op_export_details_props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'texture_name_from_image_path')
        layout.label(text=FORMAT_VERSION_LABEL)
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
        textures_folder = get_preferences().textures_folder_auto
        export_context = ExportDetailsContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.level_details_format_version = self.format_version
        export_context.textures_folder=textures_folder
        exp.export_file(bpy_obj, self.filepath, export_context)

    def invoke(self, context, event):
        preferences = get_preferences()
        self.texture_name_from_image_path = \
            preferences.details_texture_names_from_path
        self.format_version = preferences.format_version
        return super().invoke(context, event)


class XRAY_OT_pack_details_images(bpy.types.Operator):
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


def menu_func_import(self, context):
    icon = ui.icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_import_details.bl_idname, text='X-Ray level details (.details)',
        icon_value=icon
    )


def menu_func_export(self, context):
    icon = ui.icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_details.bl_idname, text='X-Ray level details (.details)',
        icon_value=icon
    )


classes = (
    (XRAY_OT_import_details, op_import_details_props),
    (XRAY_OT_export_details, op_export_details_props),
    (XRAY_OT_pack_details_images, None)
)


def register():
    for operator, props in classes:
        if props:
            assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    import_menu, export_menu = get_import_export_menus()
    export_menu.remove(menu_func_export)
    import_menu.remove(menu_func_import)
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
