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
from ... import text
from ... import utils


class ImportDetailsContext(contexts.ImportMeshContext):
    def __init__(self):
        super().__init__()
        self.format_version = None
        self.models_in_row = None
        self.load_slots = None


class ExportDetailsContext(contexts.ExportMeshContext):
    def __init__(self):
        super().__init__()
        self.level_details_format_version = None


filename_ext = '.details'
op_text = 'Level Details'


class XRAY_OT_import_details(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.details'
    bl_label = 'Import .details'
    bl_description = 'Imports X-Ray Level Details Models (.details)'
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    # file browser properties
    filter_glob = bpy.props.StringProperty(
        default='*.details',
        options={'HIDDEN'}
    )
    directory = bpy.props.StringProperty(subtype='DIR_PATH')
    filepath = bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE'}
    )
    files = bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'SKIP_SAVE'}
    )

    # import properties
    models_in_row = ie.prop_details_models_in_a_row()
    load_slots = ie.prop_details_load_slots()
    details_format = ie.prop_details_format()

    # system properties
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Import *.details')

        # check selected files
        has_files = utils.ie.has_selected_files(self)
        if not has_files:
            return {'CANCELLED'}

        # create import context
        imp_ctx = ImportDetailsContext()

        imp_ctx.operator = self
        imp_ctx.format_version = self.details_format
        imp_ctx.models_in_row = self.models_in_row
        imp_ctx.load_slots = self.load_slots

        # import
        utils.ie.import_files(
            self.directory,
            self.files,
            imp.import_file,
            imp_ctx
        )

        return {'FINISHED'}

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'levels_folder')

        layout = self.layout

        utils.draw.draw_files_count(self)

        layout.prop(self, 'models_in_row')
        layout.prop(self, 'load_slots')

        col = layout.column()
        col.active = self.load_slots

        utils.draw.draw_fmt_ver_prop(
            col,
            self,
            'details_format',
            lay_type='COLUMN'
        )

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        pref = utils.version.get_preferences()

        self.models_in_row = pref.details_models_in_a_row
        self.load_slots = pref.load_slots
        self.details_format = pref.details_format

        return super().invoke(context, event)


def search_details_obj(obj, dets_objs):
    if obj.type == 'EMPTY':
        if obj.xray.is_details:
            dets_objs.add(obj)

    if obj.parent:
        search_details_obj(obj.parent, dets_objs)


def search_details():
    dets_objs = set()

    for obj in bpy.context.selected_objects:
        search_details_obj(obj, dets_objs)

    if not dets_objs:
        active_obj = bpy.context.active_object

        if active_obj:
            search_details_obj(active_obj, dets_objs)

    return list(dets_objs)


def draw_export_props(self):    # pragma: no cover
    utils.ie.open_imp_exp_folder(self, 'levels_folder')

    layout = self.layout

    utils.draw.draw_fmt_ver_prop(
        layout,
        self,
        'format_version',
        lay_type='COLUMN',
        use_row=False
    )
    layout.prop(self, 'tex_name_from_path')


class XRAY_OT_export_details_file(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):

    bl_idname = 'xray_export.details_file'
    bl_label = 'Export .details'
    bl_options = {'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    # file browser properties
    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )

    # export properties
    tex_name_from_path = ie.PropObjectTextureNamesFromPath()
    format_version = ie.prop_details_format_version()

    # system properties
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    def draw(self, context):    # pragma: no cover
        draw_export_props(self)

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.details')

        # search details object
        dets_objs = search_details()

        if not dets_objs:
            self.report({'ERROR'}, 'Cannot find details object')
            return {'CANCELLED'}

        if len(dets_objs) > 1:
            self.report({'ERROR'}, 'Too many details objects found')
            return {'CANCELLED'}

        details_object = dets_objs[0]

        # create export context
        exp_ctx = ExportDetailsContext()

        exp_ctx.operator = self
        exp_ctx.texname_from_path = self.tex_name_from_path
        exp_ctx.level_details_format_version = self.format_version
        exp_ctx.level_name = os.path.basename(os.path.dirname(self.filepath))

        # export
        try:
            exp.export_file(details_object, self.filepath, exp_ctx)
        except log.AppError as err:
            exp_ctx.errors.append(err)

        # report errors
        for err in exp_ctx.errors:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        dets_objs = search_details()

        if not dets_objs:
            self.report({'ERROR'}, 'Cannot find details object')
            return {'CANCELLED'}

        if len(dets_objs) > 1:
            self.report({'ERROR'}, 'Too many details objects found')
            return {'CANCELLED'}

        obj = dets_objs[0]

        pref = utils.version.get_preferences()
        self.tex_name_from_path = pref.details_texture_names_from_path
        self.format_version = pref.format_version

        self.filepath = utils.ie.add_file_ext(obj.name, self.filename_ext)

        return super().invoke(context, event)


class XRAY_OT_export_details(utils.ie.BaseOperator):
    bl_idname = 'xray_export.details'
    bl_label = 'Export .details'
    bl_options = {'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    # file browser properties
    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )
    directory = bpy.props.StringProperty(subtype='DIR_PATH')

    # export properties
    tex_name_from_path = ie.PropObjectTextureNamesFromPath()
    format_version = ie.prop_details_format_version()

    # system properties
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    def draw(self, context):    # pragma: no cover
        draw_export_props(self)

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.details')

        dets_objs = search_details()

        if not dets_objs:
            self.report({'ERROR'}, 'Cannot find details object')
            return {'CANCELLED'}

        # create export context
        exp_ctx = ExportDetailsContext()

        exp_ctx.operator = self
        exp_ctx.texname_from_path = self.tex_name_from_path
        exp_ctx.level_details_format_version = self.format_version

        # collect object and paths
        objs = []
        paths = []
        for obj in dets_objs:
            file_path = os.path.join(self.directory, obj.name)
            file_path = utils.ie.add_file_ext(file_path, filename_ext)
            objs.append(obj)
            paths.append(file_path)

        # find duplicate files
        dupli_errors = []
        for obj, path in zip(objs, paths):
            if paths.count(path) > 1:
                error = log.AppError(
                    text.error.details_file_duplicates,
                    log.props(file_path=file_path, object=obj.name)
                )
                dupli_errors.append(error)

        if dupli_errors:
            for error in dupli_errors:
                log.err(error)
            return {'CANCELLED'}

        # export
        for obj, path in zip(objs, paths):
            try:
                exp_ctx.level_name = os.path.basename(os.path.dirname(path))
                exp.export_file(obj, path, exp_ctx)
            except log.AppError as err:
                exp_ctx.errors.append(err)

        # report errors
        for err in exp_ctx.errors:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        dets_objs = search_details()

        if not dets_objs:
            self.report({'ERROR'}, 'Cannot find details object')
            return {'CANCELLED'}

        if len(dets_objs) == 1:
            return bpy.ops.xray_export.details_file('INVOKE_DEFAULT')

        pref = utils.version.get_preferences()
        self.tex_name_from_path = pref.details_texture_names_from_path
        self.format_version = pref.format_version

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


class XRAY_OT_pack_details_images(utils.ie.BaseOperator):
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
    XRAY_OT_export_details_file,
    XRAY_OT_pack_details_images
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
