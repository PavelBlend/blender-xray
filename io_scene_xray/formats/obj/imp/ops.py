# blender modules
import bpy
import bpy_extras

# addon modules
from . import ctx
from . import main
from ... import ie
from .... import log
from .... import utils


filename_ext = '.object'

import_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    ),

    # *.object format props
    'fmt_version': ie.PropSDKVersion(),
    'import_motions': ie.PropObjectMotionsImport(),
    'mesh_split_by_materials': ie.PropObjectMeshSplitByMaterials(),

    'processed': bpy.props.BoolProperty(default=False, options={'HIDDEN'})
}


class XRAY_OT_import_object(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.object'
    bl_label = 'Import .object'
    bl_description = 'Imports X-Ray object'
    bl_options = {'UNDO', 'PRESET'}

    text = 'Source Object'
    ext = filename_ext
    filename_ext = filename_ext
    props = import_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Import *.object')

        # check selected files
        has_sel = utils.ie.has_selected_files(self)
        if not has_sel:
            return {'CANCELLED'}

        # set import context
        imp_ctx = ctx.ImportObjectContext()

        use_soc_sg = self.fmt_version == 'soc'

        imp_ctx.soc_sgroups = use_soc_sg
        imp_ctx.import_motions = self.import_motions
        imp_ctx.split_by_materials = self.mesh_split_by_materials
        imp_ctx.operator = self

        # import files
        utils.ie.import_files(
            self.directory,
            self.files,
            main.import_file,
            imp_ctx
        )

        return {'FINISHED'}

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'objects_folder')

        layout = self.layout

        utils.draw.draw_files_count(self)
        utils.draw.draw_fmt_ver_prop(layout, self, 'fmt_version')

        layout.prop(self, 'import_motions')
        layout.prop(self, 'mesh_split_by_materials')

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        pref = utils.version.get_preferences()

        self.fmt_version = utils.ie.get_sdk_ver(pref.sdk_version)
        self.import_motions = pref.object_motions_import
        self.mesh_split_by_materials = pref.object_mesh_split_by_mat

        return super().invoke(context, event)


def register():
    utils.version.register_operators(XRAY_OT_import_object)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_import_object)
