# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import main
from ... import ie
from ... import contexts
from .... import log
from .... import utils


class ExportOgfContext(
        contexts.ExportMeshContext,
        contexts.ExportAnimationContext
    ):
    def __init__(self):
        super().__init__()
        self.fmt_ver = None
        self.hq_export = None


op_text = 'Game Object'
filename_ext = '.ogf'


def draw_props(self, context):    # pragma: no cover
    layout = self.layout
    utils.draw.draw_fmt_ver_prop(layout, self, 'fmt_version')
    layout.prop(self, 'export_motions')
    row = layout.row()
    row.active = self.fmt_version == 'cscop' and self.export_motions
    row.prop(self, 'hq_export')
    layout.prop(self, 'use_export_paths')
    layout.prop(self, 'texture_name_from_image_path')


class XRAY_OT_export_ogf_file(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):

    bl_idname = 'xray_export.ogf_file'
    bl_label = 'Export .ogf'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )
    texture_name_from_image_path = ie.PropObjectTextureNamesFromPath()
    fmt_version = ie.PropSDKVersion()
    hq_export = ie.prop_omf_high_quality()
    use_export_paths = ie.PropUseExportPaths()
    export_motions = ie.PropObjectMotionsExport()

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'meshes_folder')
        draw_props(self, context)

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.execute_require_filepath
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.ogf')

        selected_objs = context.selected_objects
        root_objs = utils.ie.get_root_objs()

        if not root_objs:
            self.report({'ERROR'}, 'Cannot find object root')
            return {'CANCELLED'}

        exported_obj = root_objs[0]

        export_context = ExportOgfContext()
        export_context.operator = self
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.fmt_ver = self.fmt_version
        export_context.hq_export = self.hq_export
        export_context.export_motions = self.export_motions

        file_path = self.filepath
        directory, file = os.path.split(file_path)
        exp_path = utils.ie.get_export_path(exported_obj)

        if self.use_export_paths and exp_path:
            exp_dir = os.path.join(directory, exp_path)
            file_path = os.path.join(exp_dir, file)
            os.makedirs(exp_dir, exist_ok=True)

        try:
            main.export_file(exported_obj, file_path, export_context)
        except log.AppError as err:
            export_context.errors.append(err)

        for err in export_context.errors:
            log.err(err)

        for obj in selected_objs:
            utils.version.select_object(obj)

        utils.version.set_active_object(exported_obj)

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        pref = utils.version.get_preferences()

        self.texture_name_from_image_path = pref.ogf_texture_names_from_path
        self.fmt_version = utils.ie.get_sdk_ver(pref.ogf_export_fmt_ver)
        self.use_export_paths = pref.ogf_export_use_export_paths
        self.export_motions = pref.ogf_export_motions
        self.hq_export = pref.ogf_export_hq_motions

        root_objs = utils.ie.get_root_objs()

        if not root_objs:
            self.report({'ERROR'}, 'Cannot find object root')
            return {'CANCELLED'}

        if len(root_objs) > 1:
            self.report({'ERROR'}, 'Too many object roots found')
            return {'CANCELLED'}

        exported_obj = root_objs[0]

        self.filepath = utils.ie.add_file_ext(
            exported_obj.name,
            self.filename_ext
        )

        return super().invoke(context, event)


class XRAY_OT_export_ogf(utils.ie.BaseOperator):
    bl_idname = 'xray_export.ogf'
    bl_label = 'Export .ogf'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    directory = bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'HIDDEN'}
    )
    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )
    texture_name_from_image_path = ie.PropObjectTextureNamesFromPath()
    export_motions = ie.PropObjectMotionsExport()
    fmt_version = ie.PropSDKVersion()
    hq_export = ie.prop_omf_high_quality()
    use_export_paths = ie.PropUseExportPaths()
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'meshes_folder')
        draw_props(self, context)

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.ogf')

        export_context = ExportOgfContext()
        export_context.operator = self
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.export_motions = self.export_motions
        export_context.fmt_ver = self.fmt_version
        export_context.hq_export = self.hq_export

        root_objs = utils.ie.get_root_objs()

        if not root_objs:
            self.report({'ERROR'}, 'Cannot find root-objects')
            return {'CANCELLED'}

        for obj in root_objs:
            file_name = utils.ie.add_file_ext(obj.name, filename_ext)

            path = self.directory
            exp_path = utils.ie.get_export_path(obj)
            if self.use_export_paths and exp_path:
                path = os.path.join(path, exp_path)
                os.makedirs(path, exist_ok=True)
            file_path = os.path.join(path, file_name)

            try:
                main.export_file(obj, file_path, export_context)
            except log.AppError as err:
                export_context.errors.append(err)

        for err in export_context.errors:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        pref = utils.version.get_preferences()

        self.use_export_paths = pref.ogf_export_use_export_paths
        self.export_motions = pref.ogf_export_motions
        self.texture_name_from_image_path = pref.ogf_texture_names_from_path
        self.fmt_version = utils.ie.get_sdk_ver(pref.ogf_export_fmt_ver)
        self.hq_export = pref.ogf_export_hq_motions

        root_objs = utils.ie.get_root_objs()

        if not root_objs:
            self.report({'ERROR'}, 'Cannot find root-objects')
            return {'CANCELLED'}

        if len(root_objs) == 1:
            return bpy.ops.xray_export.ogf_file('INVOKE_DEFAULT')

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_export_ogf,
    XRAY_OT_export_ogf_file
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
