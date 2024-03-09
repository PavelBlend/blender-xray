# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import main
from ... import ie
from ... import contexts
from .... import utils
from .... import text
from .... import log


class ExportObjectContext(
        contexts.ExportMeshContext,
        contexts.ExportAnimationContext
    ):

    def __init__(self):
        super().__init__()
        self.soc_sgroups = None
        self.smoothing_out_of = None


def draw_props(self):    # pragma: no cover
    layout = self.layout

    utils.draw.draw_fmt_ver_prop(layout, self, 'fmt_version')

    row = layout.split()
    row.label(text='Smoothing:')
    row.row().prop(self, 'smoothing_out_of', expand=True)

    layout.prop(self, 'use_export_paths')
    layout.prop(self, 'export_motions')
    layout.prop(self, 'texture_name_from_image_path')


def find_objects_for_export(context, export_context):
    roots = utils.obj.get_root_objs(export_context)

    if not roots:
        roots = [obj for obj in context.scene.objects if obj.xray.isroot]

        if not roots:
            raise log.AppError(text.error.object_no_roots)

        if len(roots) > 1:
            raise log.AppError(text.error.object_many_roots)

    return roots


filename_ext = '.object'


class XRAY_OT_export_object(utils.ie.BaseOperator):
    bl_idname = 'xray_export.object'
    bl_label = 'Export .object'
    bl_options = {'PRESET'}

    text = 'Source Object'
    ext = filename_ext
    filename_ext = filename_ext

    # file browser properties
    directory = bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )

    # export properties
    fmt_version = ie.PropSDKVersion()
    use_export_paths = ie.PropUseExportPaths()
    smoothing_out_of = ie.prop_smoothing_out_of()
    export_motions = ie.PropObjectMotionsExport()
    texture_name_from_image_path = ie.PropObjectTextureNamesFromPath()

    # system properties
    objects = bpy.props.StringProperty(options={'HIDDEN'})
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'objects_folder')
        draw_props(self)

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.object')

        exp_ctx = ExportObjectContext()

        exp_ctx.operator = self
        exp_ctx.texname_from_path = self.texture_name_from_image_path
        exp_ctx.soc_sgroups = self.fmt_version == 'soc'
        exp_ctx.export_motions = self.export_motions
        exp_ctx.smoothing_out_of = self.smoothing_out_of

        if not self.objects:
            roots = find_objects_for_export(context, exp_ctx)
            self.objects = ','.join([obj.name for obj in roots])

        for name in self.objects.split(','):
            bpy_obj = context.scene.objects[name]
            name = utils.ie.add_file_ext(name, filename_ext)
            path = self.directory

            exp_path = utils.ie.get_export_path(bpy_obj)
            if self.use_export_paths and exp_path:
                path = os.path.join(path, exp_path)
                os.makedirs(path, exist_ok=True)

            try:
                main.export_file(
                    bpy_obj,
                    os.path.join(path, name),
                    exp_ctx
                )
            except log.AppError as err:
                exp_ctx.errors.append(err)

        for err in exp_ctx.errors:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, _event):    # pragma: no cover
        exp_ctx = ExportObjectContext()

        try:
            roots = find_objects_for_export(context, exp_ctx)
        except log.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        if len(roots) == 1:
            return bpy.ops.xray_export.object_file('INVOKE_DEFAULT')

        self.objects = ','.join([obj.name for obj in roots])

        pref = utils.version.get_preferences()

        self.fmt_version = utils.ie.get_sdk_ver(pref.export_object_sdk_version)
        self.export_motions = pref.object_motions_export
        self.texture_name_from_image_path = pref.object_texture_names_from_path
        self.smoothing_out_of = pref.smoothing_out_of
        self.use_export_paths = pref.export_object_use_export_paths

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


class XRAY_OT_export_object_file(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):

    bl_idname = 'xray_export.object_file'
    bl_label = 'Export .object'
    bl_options = {'PRESET'}

    filename_ext = '.object'

    # file browser properties
    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )

    # export properties
    texture_name_from_image_path = ie.PropObjectTextureNamesFromPath()
    fmt_version = ie.PropSDKVersion()
    use_export_paths = ie.PropUseExportPaths()
    smoothing_out_of = ie.prop_smoothing_out_of()
    export_motions = ie.PropObjectMotionsExport()

    # system properties
    object = bpy.props.StringProperty(options={'HIDDEN'})

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'objects_folder')
        draw_props(self)

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.object')

        export_context = ExportObjectContext()

        export_context.operator = self
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.soc_sgroups = self.fmt_version == 'soc'
        export_context.export_motions = self.export_motions
        export_context.smoothing_out_of = self.smoothing_out_of

        bpy_obj = context.scene.objects[self.object]

        file_path = self.filepath
        directory, file = os.path.split(file_path)
        exp_path = utils.ie.get_export_path(bpy_obj)

        if self.use_export_paths and exp_path:
            exp_dir = os.path.join(directory, exp_path)
            file_path = os.path.join(exp_dir, file)
            os.makedirs(exp_dir, exist_ok=True)

        try:
            main.export_file(bpy_obj, file_path, export_context)
        except log.AppError as err:
            export_context.errors.append(err)

        for err in export_context.errors:
            log.err(err)

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        pref = utils.version.get_preferences()
        exp_ctx = ExportObjectContext()

        try:
            roots = find_objects_for_export(context, exp_ctx)
        except log.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        if len(roots) > 1:
            self.report({'ERROR'}, 'Too many \'root\'-objects selected')
            return {'CANCELLED'}

        self.object = roots[0].name
        self.filepath = utils.ie.add_file_ext(self.object, filename_ext)

        # set defaults
        self.fmt_version = utils.ie.get_sdk_ver(pref.export_object_sdk_version)
        self.export_motions = pref.object_motions_export
        self.texture_name_from_image_path = pref.object_texture_names_from_path
        self.smoothing_out_of = pref.smoothing_out_of
        self.use_export_paths = pref.export_object_use_export_paths

        return super().invoke(context, event)


classes = (
    XRAY_OT_export_object,
    XRAY_OT_export_object_file
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
