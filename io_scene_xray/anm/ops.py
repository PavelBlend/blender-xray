# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import icons
from .. import utils
from .. import version_utils
from .. import plugin_props


def menu_func_import(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_import_anm.bl_idname,
        text=utils.build_op_label(XRAY_OT_import_anm),
        icon_value=icon
    )


def menu_func_export(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_anm.bl_idname,
        text=utils.build_op_label(XRAY_OT_export_anm),
        icon_value=icon
    )


filename_ext = '.anm'
op_text = 'Animation Paths'

op_import_anm_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    ),
    'camera_animation': plugin_props.PropAnmCameraAnimation()
}


class XRAY_OT_import_anm(
        plugin_props.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.anm'
    bl_label = 'Import .anm'
    bl_description = 'Imports X-Ray animation'
    bl_options = {'UNDO', 'PRESET'}

    draw_fun = menu_func_import
    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_import_anm_props.items():
            exec('{0} = op_import_anm_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        if not self.files[0].name:
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}
        import_context = imp.ImportAnmContext()
        import_context.camera_animation = self.camera_animation
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            file_path = os.path.join(self.directory, file.name)
            if ext == '.anm':
                if not os.path.exists(file_path):
                    self.report(
                        {'ERROR'},
                        'File not found: "{}"'.format(file_path)
                    )
                    return {'CANCELLED'}
                try:
                    imp.import_file(file_path, import_context)
                except utils.AppError as err:
                    self.report({'ERROR'}, str(err))
            else:
                self.report(
                    {'ERROR'},
                    'Not recognised format of file: "{}"'.format(file_path)
                )
                return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.camera_animation = preferences.anm_create_camera
        return super().invoke(context, event)


op_export_anm_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
}


class XRAY_OT_export_anm(
        plugin_props.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.anm'
    bl_label = 'Export .anm'
    bl_description = 'Exports X-Ray animation'

    draw_fun = menu_func_export
    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_anm_props.items():
            exec('{0} = op_export_anm_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        try:
            exp.export_file(context.active_object, self.filepath)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.active_object
        if obj:
            self.filepath = obj.name
            if not self.filepath.lower().endswith(self.filename_ext):
                self.filepath += self.filename_ext
        else:
            self.report({'ERROR'}, 'No active objects!')
            return {'CANCELLED'}
        if not obj.animation_data:
            self.report(
                {'ERROR'},
                'Object "{}" has no animation data.'.format(obj.name)
            )
            return {'CANCELLED'}
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    (XRAY_OT_import_anm, op_import_anm_props),
    (XRAY_OT_export_anm, op_export_anm_props)
)


def register():
    for operator, properties in classes:
        version_utils.assign_props([(properties, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, properties in reversed(classes):
        bpy.utils.unregister_class(operator)
