# blender modules
import bpy
import bpy_extras

# addon modules
from . import main
from ... import ie
from ... import contexts
from .... import log
from .... import text
from .... import utils


class ImportOgfContext(
        contexts.ImportMeshContext,
        contexts.ImportAnimationContext
    ):
    def __init__(self):
        super().__init__()
        pref = utils.version.get_preferences()
        self.import_bone_parts = None
        self.repored = False
        self._meshes_folders = utils.ie.get_pref_paths('meshes_folder')

    @property
    def meshes_folders(self):
        if not self._meshes_folders:
            if not self.repored:
                self.repored = True
                self.operator.report(
                    {'WARNING'},
                    text.get_text(text.warn.meshes_folder_not_spec)
                )
        return self._meshes_folders


op_text = 'Game Object'
filename_ext = '.ogf'


class XRAY_OT_import_ogf(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.ogf'
    bl_label = 'Import .ogf'
    bl_description = 'Import X-Ray Compiled Game Model (.ogf)'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    filter_glob = bpy.props.StringProperty(
        default='*.ogf',
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
    import_motions = ie.PropObjectMotionsImport()
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Import *.ogf')

        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}

        import_context = ImportOgfContext()

        import_context.operator = self
        import_context.import_motions = self.import_motions
        import_context.import_bone_parts = True
        import_context.add_to_motion_list = True

        utils.ie.import_files(
            self.directory,
            self.files,
            main.import_file,
            import_context
        )

        return {'FINISHED'}

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'meshes_folder')
        layout = self.layout
        utils.draw.draw_files_count(self)
        layout.prop(self, 'import_motions')

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        preferences = utils.version.get_preferences()
        self.import_motions = preferences.ogf_import_motions
        return super().invoke(context, event)


def register():
    utils.version.register_classes(XRAY_OT_import_ogf)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_import_ogf)
