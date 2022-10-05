# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import ie
from ... import utils
from ... import log


op_text = 'Scene Selection'
filename_ext = '.level'

export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
    ),
}


class XRAY_OT_export_scene_selection(
        ie.BaseOperator, bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.scene'
    bl_label = 'Export .level'

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        try:
            self.export(self.objs, context)
        except log.AppError as err:
            log.err(err)
        return {'FINISHED'}

    def export(self, bpy_objs, context):
        exp.export_file(bpy_objs, self.filepath)

    def invoke(self, context, event):

        self.objs = context.selected_objects

        if not self.objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}

        return super().invoke(context, event)


import_props = {
    'filepath': bpy.props.StringProperty(subtype="FILE_PATH"),
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
    ),
    'mesh_split_by_materials': ie.PropObjectMeshSplitByMaterials(),
    'fmt_version': ie.PropSDKVersion()
}


class XRAY_OT_import_scene_selection(
        ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.scene'
    bl_label = 'Import .level'
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
        try:
            imp.import_file(self.filepath, self)
        except log.AppError as err:
            log.err(err)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = utils.version.get_preferences()
        self.mesh_split_by_materials = preferences.scene_selection_mesh_split_by_mat
        self.fmt_version = preferences.scene_selection_sdk_version
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_import_scene_selection,
    XRAY_OT_export_scene_selection
)


def register():
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
