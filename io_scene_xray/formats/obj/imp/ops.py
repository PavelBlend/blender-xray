# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import utility
from .. import imp
from ... import ie
from .... import icons
from .... import log
from .... import utils


import_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.object', options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype="DIR_PATH"),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    ),
    'import_motions': ie.PropObjectMotionsImport(),
    'mesh_split_by_materials': ie.PropObjectMeshSplitByMaterials(),
    'fmt_version': ie.PropSDKVersion()
}

filename_ext = '.object'


class XRAY_OT_import_object(ie.BaseOperator, bpy_extras.io_utils.ImportHelper):
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
    @utils.set_cursor_state
    def execute(self, context):
        preferences = utils.version.get_preferences()
        textures_folder = preferences.textures_folder_auto
        objects_folder = preferences.objects_folder_auto
        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')
        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}
        import_context = utility.ImportObjectContext()
        import_context.textures_folder=textures_folder
        import_context.soc_sgroups=self.fmt_version == 'soc'
        import_context.import_motions=self.import_motions
        import_context.split_by_materials=self.mesh_split_by_materials
        import_context.operator=self
        import_context.objects_folder=objects_folder
        for file in self.files:
            file_path = os.path.join(self.directory, file.name)
            import_context.before_import_file()
            try:
                imp.import_file(file_path, import_context)
            except log.AppError as err:
                import_context.errors.append(err)
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        utils.draw.draw_files_count(self)
        utils.draw.draw_fmt_ver_prop(layout, self, 'fmt_version')

        layout.prop(self, 'import_motions')
        layout.prop(self, 'mesh_split_by_materials')

    def invoke(self, context, event):
        preferences = utils.version.get_preferences()
        self.fmt_version = preferences.sdk_version
        self.import_motions = preferences.object_motions_import
        self.mesh_split_by_materials = preferences.object_mesh_split_by_mat
        return super().invoke(context, event)


def register():
    utils.version.register_operators(XRAY_OT_import_object)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_import_object)
