# blender modules
import bpy
import bpy_extras

# addon modules
from . import main
from ... import ie
from ... import contexts
from .... import log
from .... import utils


class ImportOgfContext(
        contexts.ImportMeshContext,
        contexts.ImportAnimationContext
    ):
    def __init__(self):
        super().__init__()
        self.meshes_folder = None
        self.import_bone_parts = None


op_text = 'Game Object'
filename_ext = '.ogf'


import_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.ogf', options={'HIDDEN'}
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
    'import_motions': ie.PropObjectMotionsImport()
}


class XRAY_OT_import_ogf(
        ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.ogf'
    bl_label = 'Import .ogf'
    bl_description = 'Import X-Ray Compiled Game Model (.ogf)'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

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
        prefs = utils.version.get_preferences()
        textures_folder = prefs.textures_folder_auto
        meshes_folder = prefs.meshes_folder_auto
        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')
        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}
        import_context = ImportOgfContext()
        import_context.textures_folder = textures_folder
        import_context.meshes_folder = meshes_folder
        import_context.import_motions = self.import_motions
        import_context.import_bone_parts = True
        import_context.add_actions_to_motion_list = True

        utils.ie.import_files(
            self.directory,
            self.files,
            main.import_file,
            import_context
        )

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        utils.draw.draw_files_count(self)
        layout.prop(self, 'import_motions')

    def invoke(self, context, event):
        preferences = utils.version.get_preferences()
        self.import_motions = preferences.ogf_import_motions
        return super().invoke(context, event)
