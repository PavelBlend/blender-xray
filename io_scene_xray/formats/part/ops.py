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
from .. import obj
from ... import utils
from ... import text
from ... import log


class ImportPartContext(obj.imp.ctx.ImportObjectContext):
    pass


class ExportPartContext(contexts.ExportContext):
    def __init__(self):
        super().__init__()
        self.fmt_ver = None


filename_ext = '.part'
op_text = 'Scene Objects'


class XRAY_OT_import_part(utils.ie.BaseOperator):
    bl_idname = 'xray_import.part'
    bl_label = 'Import .part'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    directory = bpy.props.StringProperty(subtype='DIR_PATH')
    files = bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    )
    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )
    mesh_split_by_materials = ie.PropObjectMeshSplitByMaterials()
    fmt_version = ie.PropSDKVersion()
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        utils.draw.draw_fmt_ver_prop(layout, self, 'fmt_version')
        layout.prop(self, 'mesh_split_by_materials')

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Import *.part')

        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}

        import_context = ImportPartContext()
        import_context.soc_sgroups = self.fmt_version == 'soc'
        import_context.split_by_materials = self.mesh_split_by_materials
        import_context.operator = self
        import_context.import_motions = False

        for file in self.files:
            file_path = os.path.join(self.directory, file.name)

            try:
                imp.import_file(file_path, import_context)
            except log.AppError as err:
                import_context.errors.append(err)

        for err in import_context.errors:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        pref = utils.version.get_preferences()

        self.mesh_split_by_materials = pref.part_mesh_split_by_mat
        self.fmt_version = utils.ie.get_sdk_ver(pref.part_sdk_version)

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class XRAY_OT_export_part(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):

    bl_idname = 'xray_export.part'
    bl_label = 'Export .part'

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    # file browser properties
    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )

    # export properties
    fmt_ver = ie.PropSDKVersion()

    # system properties
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    def draw(self, context):    # pragma: no cover
        layout = self.layout

        utils.draw.draw_fmt_ver_prop(layout, self, 'fmt_ver')

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.part')

        exp_ctx = ExportPartContext()

        exp_ctx.filepath = self.filepath
        exp_ctx.operator = self
        exp_ctx.fmt_ver = self.fmt_ver

        objs = context.selected_objects

        try:
            exp.export_file(exp_ctx, objs)

        except log.AppError as err:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        objs = context.selected_objects

        if not objs:
            self.report({'ERROR'}, text.error.no_selected_obj)
            return {'CANCELLED'}

        pref = utils.version.get_preferences()

        self.fmt_ver = utils.ie.get_sdk_ver(pref.part_exp_sdk_ver)

        return super().invoke(context, event)


classes = (
    XRAY_OT_import_part,
    XRAY_OT_export_part
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
