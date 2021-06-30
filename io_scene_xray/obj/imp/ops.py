import os

import bpy
import bpy_extras

from ... import ops, plugin, plugin_prefs, registry, utils, prefs
from ...version_utils import assign_props, IS_28
from .. import imp, props as general_obj_props
from . import utils as imp_utils, props


op_import_object_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.object', options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype="DIR_PATH"),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    ),
    'import_motions': props.PropObjectMotionsImport(),
    'mesh_split_by_materials': props.PropObjectMeshSplitByMaterials(),
    'use_motion_prefix_name': props.PropObjectUseMotionPrefixName(),
    'shaped_bones': props.PropObjectBonesCustomShapes(),
    'fmt_version': general_obj_props.PropSDKVersion()
}


@registry.module_thing
class OpImportObject(ops.BaseOperator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'xray_import.object'
    bl_label = 'Import .object'
    bl_description = 'Imports X-Ray object'
    bl_options = {'UNDO', 'PRESET'}

    if not IS_28:
        for prop_name, prop_value in op_import_object_props.items():
            exec('{0} = op_import_object_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, _context):
        textures_folder = prefs.utils.get_preferences().textures_folder_auto
        objects_folder = prefs.utils.get_preferences().objects_folder_auto
        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')
        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        import_context = imp_utils.ImportObjectContext()
        import_context.textures_folder=textures_folder
        import_context.soc_sgroups=self.fmt_version == 'soc'
        import_context.import_motions=self.import_motions
        import_context.split_by_materials=self.mesh_split_by_materials
        import_context.operator=self
        import_context.use_motion_prefix_name=self.use_motion_prefix_name
        import_context.objects_folder=objects_folder
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            if ext == '.object':
                file_path = os.path.join(self.directory, file.name)
                if not os.path.exists(file_path):
                    self.report(
                        {'ERROR'}, 'File not found "{}"'.format(file_path)
                    )
                else:
                    import_context.before_import_file()
                    imp.import_file(file_path, import_context)
            else:
                self.report(
                    {'ERROR'}, 'Format of "{}" not recognised'.format(file.name)
                )
        return {'FINISHED'}

    def draw(self, _context):
        layout = self.layout
        row = layout.row()
        row.enabled = False
        row.label(text='%d items' % len(self.files))

        row = layout.split()
        row.label(text='Format Version:')
        row.row().prop(self, 'fmt_version', expand=True)

        layout.prop(self, 'import_motions')
        row = layout.row()
        row.active = self.import_motions
        row.prop(self, 'use_motion_prefix_name')
        layout.prop(self, 'mesh_split_by_materials')
        layout.prop(self, 'shaped_bones')

    def invoke(self, context, event):
        preferences = prefs.utils.get_preferences()
        self.fmt_version = preferences.sdk_version
        self.import_motions = preferences.object_motions_import
        self.mesh_split_by_materials = preferences.object_mesh_split_by_mat
        self.shaped_bones = preferences.object_bones_custom_shapes
        self.use_motion_prefix_name = preferences.use_motion_prefix_name
        return super().invoke(context, event)


assign_props([
    (op_import_object_props, OpImportObject),
])


def menu_func_import(self, _context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        OpImportObject.bl_idname,
        text='X-Ray object (.object)',
        icon_value=icon
    )
