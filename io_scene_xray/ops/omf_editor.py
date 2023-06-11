# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import utils
from .. import formats
from .. import text
from .. import log


OMF_EXT = '.omf'
op_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+OMF_EXT,
        options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'filepath': bpy.props.StringProperty(
        subtype="FILE_PATH",
        options={'SKIP_SAVE', 'HIDDEN'}
    )
}


class XRAY_OT_save_omf(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.save_omf'
    bl_label = 'Save OMF'
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props
    filename_ext = OMF_EXT

    omf_data = None

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def execute(self, context):
        path = os.path.join(self.directory, self.filepath)

        with open(path, 'wb') as file:
            file.write(XRAY_OT_save_omf.omf_data)

        XRAY_OT_save_omf.omf_data = None

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        self.filepath = 'merged.omf'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def check(self, context):    # pragma: no cover
        change_ext = False
        filepath = self.filepath

        if os.path.basename(filepath):
            file_name, ext = os.path.splitext(filepath)
            filepath = bpy.path.ensure_ext(file_name, self.filename_ext)
            if filepath != self.filepath:
                self.filepath = filepath
                change_ext = True

        return change_ext


op_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+OMF_EXT,
        options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'SKIP_SAVE'}
    )
}


class XRAY_OT_merge_omf(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.merge_omf'
    bl_label = 'Merge OMF'
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props
    filename_ext = OMF_EXT

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @log.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        omf_files = [
            os.path.join(self.directory, file.name)
            for file in self.files
                if file.name
        ]

        if not len(omf_files):
            self.report(
                {'ERROR'},
                text.get_text(text.error.no_sel_files)
            )
            return {'CANCELLED'}

        if len(omf_files) == 1:
            self.report(
                {'ERROR'},
                text.get_text(text.error.few_files)
            )
            return {'CANCELLED'}

        try:
            merged_data = formats.omf.merge.merge_files(omf_files)
        except log.AppError as err:
            log.err(err)
            return {'CANCELLED'}

        XRAY_OT_save_omf.omf_data = merged_data

        return bpy.ops.io_scene_xray.save_omf('INVOKE_DEFAULT')

    def invoke(self, context, event):    # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (XRAY_OT_save_omf, XRAY_OT_merge_omf)


def register():
    for op_class in classes:
        utils.version.register_operators(op_class)


def unregister():
    for op_class in reversed(classes):
        bpy.utils.unregister_class(op_class)
