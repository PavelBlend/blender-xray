# standart modules
import os

# blender modules
import bpy

# addon modules
from . import imp
from .. import ie
from .. import obj
from ... import utils
from ... import log


class ImportGroupContext(obj.imp.ctx.ImportObjectContext):
    pass


filename_ext = '.group'
op_text = 'Scene Objects'


class XRAY_OT_import_group(utils.ie.BaseOperator):
    bl_idname = 'xray_import.group'
    bl_label = 'Import .group'
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
    mesh_split_by_mat = ie.PropObjectMeshSplitByMaterials()
    fmt_version = ie.PropSDKVersion()
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        utils.draw.draw_fmt_ver_prop(layout, self, 'fmt_version')
        layout.prop(self, 'mesh_split_by_mat')

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Import *.group')

        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}

        import_context = ImportGroupContext()
        import_context.soc_sgroups = self.fmt_version == 'soc'
        import_context.split_by_materials = self.mesh_split_by_mat
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

        self.mesh_split_by_mat = pref.group_split_by_mat
        self.fmt_version = utils.ie.get_sdk_ver(pref.group_sdk_ver)

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    utils.version.register_classes(XRAY_OT_import_group)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_import_group)
