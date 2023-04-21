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


def get_objects(context):
    objects_list = []
    for obj in context.selected_objects:
        if obj.animation_data:
            objects_list.append(obj)
    return objects_list


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
        utils.ie.BaseOperator,
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
        utils.ie.open_imp_exp_folder(self, 'gamedata_folder')
        layout = self.layout
        utils.draw.draw_files_count(self)
        layout.prop(self, 'camera_animation')

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        has_files = utils.ie.has_selected_files(self)
        if not has_files:
            return {'CANCELLED'}

        imp_ctx = imp.ImportAnmContext()
        imp_ctx.camera_animation = self.camera_animation

        imp_fun = imp.import_file
        results = []

        utils.ie.import_files(
            self.directory,
            self.files,
            imp_fun,
            imp_ctx,
            results
        )

        if results:
            # search min and max frame range
            frame_start = min(results, key=lambda x: x[0])[0]
            frame_end = max(results, key=lambda x: x[1])[1]

            # set action frame range
            scn = context.scene
            scn.frame_start = frame_start
            scn.frame_end = frame_end

        return {'FINISHED'}

    def invoke(self, context, event):
        pref = utils.version.get_preferences()
        self.camera_animation = pref.anm_create_camera

        return super().invoke(context, event)


export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'format_version': ie.prop_anm_format_version()
}


class XRAY_OT_export_anm_file(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.anm_file'
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
        utils.ie.open_imp_exp_folder(self, 'gamedata_folder')
        layout = self.layout
        utils.draw.draw_fmt_ver_prop(layout, self, 'format_version')

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        objects_list = get_objects(context)
        if len(objects_list) == 1:
            obj = objects_list[0]
        else:
            obj = context.active_object

        export_context = exp.ExportAnmContext()
        export_context.format_version = self.format_version
        export_context.active_object = obj
        export_context.filepath = self.filepath
        try:
            exp.export_file(export_context)
        except log.AppError as err:
            export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        return {'FINISHED'}

    def invoke(self, context, event):
        objects_list = get_objects(context)
        if len(objects_list) == 1:
            obj = objects_list[0]
        else:
            obj = context.active_object

        if obj:
            self.filepath = utils.ie.add_file_ext(obj.name, filename_ext)
        else:
            self.report({'ERROR'}, 'No active objects!')
            return {'CANCELLED'}

        if not obj.animation_data:
            self.report(
                {'ERROR'},
                'Object "{}" has no animation data.'.format(obj.name)
            )
            return {'CANCELLED'}

        pref = utils.version.get_preferences()
        self.format_version = pref.anm_format_version

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'format_version': ie.prop_anm_format_version()
}


class XRAY_OT_export_anm(utils.ie.BaseOperator):
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

    objects_list = []

    def draw(self, context):
        utils.ie.open_imp_exp_folder(self, 'gamedata_folder')
        layout = self.layout
        utils.draw.draw_fmt_ver_prop(layout, self, 'format_version')

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        export_context = exp.ExportAnmContext()
        export_context.format_version = self.format_version

        objects_list = get_objects(context)

        try:
            for obj in objects_list:
                export_context.active_object = obj
                filepath = os.path.join(self.directory, obj.name)
                filepath = utils.ie.add_file_ext(filepath, filename_ext)
                export_context.filepath = filepath
                exp.export_file(export_context)

        except log.AppError as err:
            export_context.errors.append(err)

        for err in export_context.errors:
            log.err(err)

        return {'FINISHED'}

    def invoke(self, context, event):
        selected_objects_count = len(context.selected_objects)

        if not selected_objects_count:
            self.report({'ERROR'}, 'No selected object')
            return {'CANCELLED'}

        self.objects_list = get_objects(context)

        if not self.objects_list:
            self.report({'ERROR'}, 'Selected objects has no animation data')
            return {'CANCELLED'}

        if len(self.objects_list) == 1:
            return bpy.ops.xray_export.anm_file('INVOKE_DEFAULT')

        pref = utils.version.get_preferences()
        self.format_version = pref.anm_format_version

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_import_anm,
    XRAY_OT_export_anm,
    XRAY_OT_export_anm_file
)


def register():
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
