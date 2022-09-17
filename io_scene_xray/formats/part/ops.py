# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from .. import ie
from .. import obj
from .. import contexts
from ... import utils
from ... import log


class ImportPartContext(obj.imp.utility.ImportObjectContext):
    def __init__(self):
        super().__init__()


filename_ext = '.part'
op_text = 'Scene Objects'
import_props = {
    'directory': bpy.props.StringProperty(subtype="DIR_PATH"),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    ),
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
    ),
    'mesh_split_by_materials': ie.PropObjectMeshSplitByMaterials(),
    'fmt_version': ie.PropSDKVersion()
}


class XRAY_OT_import_part(ie.BaseOperator):
    bl_idname = 'xray_import.part'
    bl_label = 'Import .part'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = import_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        utils.draw.draw_fmt_ver_prop(layout, self, 'fmt_version')
        layout.prop(self, 'mesh_split_by_materials')

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}
        preferences = utils.version.get_preferences()
        textures_folder = preferences.textures_folder_auto
        objects_folder = preferences.objects_folder_auto
        import_context = ImportPartContext()
        import_context.textures_folder=textures_folder
        import_context.soc_sgroups=self.fmt_version == 'soc'
        import_context.split_by_materials=self.mesh_split_by_materials
        import_context.operator=self
        import_context.objects_folder=objects_folder
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

    def invoke(self, context, event):
        preferences = utils.version.get_preferences()
        self.mesh_split_by_materials = preferences.part_mesh_split_by_mat
        self.fmt_version = preferences.part_sdk_version
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    utils.version.register_operators(XRAY_OT_import_part)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_import_part)
