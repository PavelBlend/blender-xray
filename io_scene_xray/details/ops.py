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
from .. import utils
from .. import contexts
from .. import ie_props
from .. import draw_utils
from .. import version_utils


class ImportDetailsContext(contexts.ImportMeshContext):
    def __init__(self):
        super().__init__()
        self.format_version = None
        self.details_models_in_a_row = None
        self.load_slots = None


class ExportDetailsContext(contexts.ExportMeshContext):
    def __init__(self):
        super().__init__()
        self.level_details_format_version = None


filename_ext = '.details'
op_text = 'Level Details'


import_props = {
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
    'details_models_in_a_row': ie_props.prop_details_models_in_a_row(),
    'load_slots': ie_props.prop_details_load_slots(),
    'details_format': ie_props.prop_details_format()
}


class XRAY_OT_import_details(
        ie_props.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.details'
    bl_label = 'Import .details'
    bl_description = 'Imports X-Ray Level Details Models (.details)'
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}

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

        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}

        import_context = ImportDetailsContext()
        import_context.textures_folder=textures_folder
        import_context.operator=self
        import_context.format_version = self.details_format
        import_context.details_models_in_a_row = self.details_models_in_a_row
        import_context.load_slots = self.load_slots

        for file in self.files:
            file_ext = os.path.splitext(file.name)[-1].lower()
            if file_ext == '.details':
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

    def draw(self, context):
        layout = self.layout

        draw_utils.draw_files_count(self)

        layout.prop(self, 'details_models_in_a_row')
        layout.prop(self, 'load_slots')

        col = layout.column()
        col.active = self.load_slots

        draw_utils.draw_fmt_ver_prop(
            col,
            self,
            'details_format',
            lay_type='COLUMN'
        )

    def invoke(self, context, event):
        prefs = version_utils.get_preferences()
        self.details_models_in_a_row = prefs.details_models_in_a_row
        self.load_slots = prefs.load_slots
        self.details_format = prefs.details_format
        return super().invoke(context, event)


export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
    ),

    'texture_name_from_image_path': \
        ie_props.PropObjectTextureNamesFromPath(),

    'format_version': ie_props.prop_details_format_version()
}


class XRAY_OT_export_details(
        ie_props.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.details'
    bl_label = 'Export .details'
    bl_options = {'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'texture_name_from_image_path')
        draw_utils.draw_fmt_ver_prop(
            layout,
            self,
            'format_version',
            lay_type='COLUMN',
            use_row=False
        )

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
            self.report({'ERROR'}, 'The selected object is not empty')
            return {'CANCELLED'}

        textures_folder = version_utils.get_preferences().textures_folder_auto
        export_context = ExportDetailsContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.level_details_format_version = self.format_version
        export_context.textures_folder=textures_folder
        export_context.unique_errors = set()

        try:
            exp.export_file(objs[0], self.filepath, export_context)
        except utils.AppError as err:
            export_context.errors.append(err)

        for err in export_context.errors:
            log.err(err)

        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.object
        if not obj:
            self.report({'ERROR'}, 'No active object.')
            return {'FINISHED'}
        preferences = version_utils.get_preferences()
        self.texture_name_from_image_path = \
            preferences.details_texture_names_from_path
        self.format_version = preferences.format_version
        self.filepath = obj.name
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

        slots_images = [
            lights_image,
            hemi_image,
            shadows_image,
            mesh_0_image,
            mesh_1_image,
            mesh_2_image,
            mesh_3_image
        ]

        for image in slots_images:
            if image:
                if version_utils.IS_28:
                    image.pack()
                else:
                    image.pack(as_png=True)

        return {'FINISHED'}


classes = (
    XRAY_OT_import_details,
    XRAY_OT_export_details,
    XRAY_OT_pack_details_images
)


def register():
    version_utils.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
