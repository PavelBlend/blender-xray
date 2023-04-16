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
    'directory': bpy.props.StringProperty(subtype="DIR_PATH"),
    'filepath': bpy.props.StringProperty(
        subtype="FILE_PATH", options={'SKIP_SAVE'}
    ),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement, options={'SKIP_SAVE'}
    ),
    'details_models_in_a_row': ie.prop_details_models_in_a_row(),
    'load_slots': ie.prop_details_load_slots(),
    'details_format': ie.prop_details_format()
}


class XRAY_OT_import_details(
        ie.BaseOperator,
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

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}

        import_context = ImportDetailsContext()

        import_context.operator=self
        import_context.format_version = self.details_format
        import_context.details_models_in_a_row = self.details_models_in_a_row
        import_context.load_slots = self.load_slots

        for file in self.files:
            file_ext = os.path.splitext(file.name)[-1].lower()
            try:
                imp.import_file(
                    os.path.join(self.directory, file.name),
                    import_context
                )
            except log.AppError as err:
                import_context.errors.append(err)
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    def draw(self, context):
        utils.ie.open_imp_exp_folder(self, 'levels_folder')

        layout = self.layout

        utils.draw.draw_files_count(self)

        layout.prop(self, 'details_models_in_a_row')
        layout.prop(self, 'load_slots')

        col = layout.column()
        col.active = self.load_slots

        utils.draw.draw_fmt_ver_prop(
            col,
            self,
            'details_format',
            lay_type='COLUMN'
        )

    def invoke(self, context, event):
        prefs = utils.version.get_preferences()
        self.details_models_in_a_row = prefs.details_models_in_a_row
        self.load_slots = prefs.load_slots
        self.details_format = prefs.details_format
        return super().invoke(context, event)


export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
    ),

    'texture_name_from_image_path': \
        ie.PropObjectTextureNamesFromPath(),

    'format_version': ie.prop_details_format_version()
}


class XRAY_OT_export_details(
        ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.details'
    bl_label = 'Export .details'
    bl_options = {'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        utils.ie.open_imp_exp_folder(self, 'levels_folder')

        layout = self.layout

        utils.draw.draw_fmt_ver_prop(
            layout,
            self,
            'format_version',
            lay_type='COLUMN',
            use_row=False
        )
        layout.prop(self, 'texture_name_from_image_path')

    def search_details(self, obj, dets_objs):
        if obj.type == 'EMPTY':
            if obj.xray.is_details:
                dets_objs.add(obj)
        if obj.parent:
            self.search_details(obj.parent, dets_objs)

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        dets_objs = set()
        for obj in context.selected_objects:
            self.search_details(obj, dets_objs)

        if not dets_objs:
            self.report({'ERROR'}, 'Cannot find details object')
            return {'CANCELLED'}

        if len(dets_objs) > 1:
            self.report({'ERROR'}, 'Too many details objects found')
            return {'CANCELLED'}

        deteils_object = list(dets_objs)[0]

        export_context = ExportDetailsContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.level_details_format_version = self.format_version
        export_context.unique_errors = set()

        try:
            exp.export_file(deteils_object, self.filepath, export_context)
        except log.AppError as err:
            export_context.errors.append(err)

        for err in export_context.errors:
            log.err(err)

        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, 'No active object.')
            return {'FINISHED'}
        preferences = utils.version.get_preferences()
        self.texture_name_from_image_path = \
            preferences.details_texture_names_from_path
        self.format_version = preferences.format_version
        self.filepath = utils.ie.add_file_ext(obj.name, self.filename_ext)
        return super().invoke(context, event)


class XRAY_OT_pack_details_images(bpy.types.Operator):
    bl_idname = 'io_scene_xray.pack_details_images'
    bl_label = 'Pack Details Images'
    bl_description = 'Pack Details Images as PNG'

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if context.active_object.type == 'EMPTY':
                return True
        return False

    @utils.ie.set_initial_state
    def execute(self, context):
        slots = context.active_object.xray.detail.slots
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
                if utils.version.IS_28:
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
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
