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


class XRAY_OT_merge_omf(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.merge_omf'
    bl_label = 'Merge OMF'
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = OMF_EXT

    omf_data = None

    filter_glob = bpy.props.StringProperty(
        default='*'+OMF_EXT,
        options={'HIDDEN'}
    )
    directory = bpy.props.StringProperty(subtype='DIR_PATH')
    filepath = bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE', 'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        return context.scene.xray.merge_omf.omf_files

    def execute(self, context):
        path = os.path.join(self.directory, self.filepath)

        omf_files = []
        for omf in context.scene.xray.merge_omf.omf_files:
            if omf.file_path not in omf_files:
                omf_files.append(omf.file_path)

        try:
            merged_data = formats.omf.merge.merge_files(omf_files)
        except log.AppError as err:
            log.err(err)
            return {'CANCELLED'}

        with open(path, 'wb') as file:
            file.write(merged_data)

        XRAY_OT_merge_omf.omf_data = None

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


class XRAY_OT_add_omf(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.add_omf'
    bl_label = 'Add OMF Files'
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = OMF_EXT

    filter_glob = bpy.props.StringProperty(
        default='*'+OMF_EXT,
        options={'HIDDEN'}
    )
    directory = bpy.props.StringProperty(subtype='DIR_PATH')
    files = bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'SKIP_SAVE'}
    )

    @log.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        omf_files = [
            os.path.join(self.directory, file.name)
            for file in self.files
                if file.name
        ]

        if not len(omf_files):
            self.report({'ERROR'}, text.error.no_sel_files)
            return {'CANCELLED'}

        if len(omf_files) == 1:
            self.report({'ERROR'}, text.error.few_files)
            return {'CANCELLED'}

        for file_path in omf_files:
            omf = context.scene.xray.merge_omf.omf_files.add()
            omf.file_path = file_path
            omf.file_name = os.path.basename(file_path)

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (XRAY_OT_merge_omf, XRAY_OT_add_omf)


def register():
    for op_class in classes:
        utils.version.register_classes(op_class)


def unregister():
    for op_class in reversed(classes):
        bpy.utils.unregister_class(op_class)
