# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import ie
from .. import obj
from ... import utils
from ... import log


class ImportSceneContext(obj.imp.ctx.ImportObjectMeshContext):
    pass


op_text = 'Scene Selection'
filename_ext = '.level'


class XRAY_OT_export_scene(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):

    bl_idname = 'xray_export.scene'
    bl_label = 'Export .level'

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.level')

        objs = context.selected_objects

        try:
            self.export(objs, context)

        except log.AppError as err:
            log.err(err)

        return {'FINISHED'}

    def export(self, bpy_objs, context):
        exp.export_file(bpy_objs, self.filepath)

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        objs = context.selected_objects

        if not objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}

        return super().invoke(context, event)


class XRAY_OT_import_scene(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.scene'
    bl_label = 'Import .level'
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
        utils.stats.update('Import *.level')

        imp_context = ImportSceneContext()

        imp_context.import_motions = False
        imp_context.soc_sgroups = self.fmt_version == 'soc'
        imp_context.split_by_materials = self.mesh_split_by_materials
        imp_context.operator = self
        imp_context.before_import_file()

        # import files
        utils.ie.import_files(
            self.directory,
            self.files,
            imp.import_file,
            imp_context
        )

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        pref = utils.version.get_preferences()

        self.mesh_split_by_materials = pref.scene_selection_mesh_split_by_mat
        self.fmt_version = utils.ie.get_sdk_ver(pref.scene_selection_sdk_version)

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_import_scene,
    XRAY_OT_export_scene
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
