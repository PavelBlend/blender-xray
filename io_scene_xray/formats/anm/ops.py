# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import ie
from ... import log
from ... import utils


filename_ext = '.anm'
op_text = 'Animation Paths'

import_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    ),
    'camera_animation': ie.PropAnmCameraAnimation()
}


class XRAY_OT_import_anm(
        ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.anm'
    bl_label = 'Import .anm'
    bl_description = 'Imports X-Ray animation'
    bl_options = {'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = import_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        utils.draw.draw_files_count(self)
        layout.prop(self, 'camera_animation')

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        if not self.files[0].name:
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}
        import_context = imp.ImportAnmContext()
        import_context.camera_animation = self.camera_animation
        files_count = 0
        for file in self.files:
            import_context.filepath = os.path.join(self.directory, file.name)
            try:
                frame_start, frame_end = imp.import_file(import_context)
                files_count += 1
            except log.AppError as err:
                import_context.errors.append(err)
        if files_count == 1:
            # set action frame range
            scn = context.scene
            scn.frame_start = frame_start
            scn.frame_end = frame_end
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = utils.version.get_preferences()
        self.camera_animation = preferences.anm_create_camera
        return super().invoke(context, event)


export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'format_version': ie.prop_anm_format_version()
}


class XRAY_OT_export_anm(
        ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.anm'
    bl_label = 'Export .anm'
    bl_description = 'Exports X-Ray animation'
    bl_options = {'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        utils.draw.draw_fmt_ver_prop(layout, self, 'format_version')

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        export_context = exp.ExportAnmContext()
        export_context.format_version = self.format_version
        export_context.active_object = context.active_object
        export_context.filepath = self.filepath
        try:
            exp.export_file(export_context)
        except log.AppError as err:
            export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
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
        preferences = utils.version.get_preferences()
        self.format_version = preferences.anm_format_version
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_import_anm,
    XRAY_OT_export_anm
)


def register():
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
