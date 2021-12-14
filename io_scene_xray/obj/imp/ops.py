# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import utility
from .. import imp
from ... import icons
from ... import log
from ... import utils
from ... import version_utils
from ... import ie_props


def menu_func_import(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_import_object.bl_idname,
        text=utils.build_op_label(XRAY_OT_import_object),
        icon_value=icon
    )


op_import_object_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.object', options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype="DIR_PATH"),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    ),
    'import_motions': ie_props.PropObjectMotionsImport(),
    'mesh_split_by_materials': ie_props.PropObjectMeshSplitByMaterials(),
    'use_motion_prefix_name': ie_props.PropObjectUseMotionPrefixName(),
    'fmt_version': ie_props.PropSDKVersion()
}

filename_ext = '.object'


class XRAY_OT_import_object(ie_props.BaseOperator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'xray_import.object'
    bl_label = 'Import .object'
    bl_description = 'Imports X-Ray object'
    bl_options = {'UNDO', 'PRESET'}

    draw_fun = menu_func_import
    text = 'Source Object'
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_import_object_props.items():
            exec('{0} = op_import_object_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        preferences = version_utils.get_preferences()
        textures_folder = preferences.textures_folder_auto
        objects_folder = preferences.objects_folder_auto
        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')
        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        import_context = utility.ImportObjectContext()
        import_context.textures_folder=textures_folder
        import_context.soc_sgroups=self.fmt_version == 'soc'
        import_context.import_motions=self.import_motions
        import_context.split_by_materials=self.mesh_split_by_materials
        import_context.operator=self
        import_context.use_motion_prefix_name=self.use_motion_prefix_name
        import_context.objects_folder=objects_folder
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            file_path = os.path.join(self.directory, file.name)
            if not os.path.exists(file_path):
                self.report(
                    {'ERROR'}, 'File not found "{}"'.format(file_path)
                )
            else:
                try:
                    import_context.before_import_file()
                    imp.import_file(file_path, import_context)
                except utils.AppError as err:
                    import_context.errors.append(err)
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.enabled = False
        files_count = len(self.files)
        if files_count == 1:
            if not self.files[0].name:
                files_count = 0
        row.label(text='{} items'.format(files_count))

        row = layout.split()
        row.label(text='Format Version:')
        row.row().prop(self, 'fmt_version', expand=True)

        layout.prop(self, 'import_motions')
        row = layout.row()
        row.active = self.import_motions
        row.prop(self, 'use_motion_prefix_name')
        layout.prop(self, 'mesh_split_by_materials')

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.fmt_version = preferences.sdk_version
        self.import_motions = preferences.object_motions_import
        self.mesh_split_by_materials = preferences.object_mesh_split_by_mat
        self.use_motion_prefix_name = preferences.use_motion_prefix_name
        return super().invoke(context, event)


def register():
    version_utils.assign_props([
        (op_import_object_props, XRAY_OT_import_object),
    ])
    bpy.utils.register_class(XRAY_OT_import_object)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_import_object)
