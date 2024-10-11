# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import formats
from .. import utils
from .. import log
from .. import text
from .. import rw


class XRAY_OT_remove_all_omfs(bpy.types.Operator):
    bl_idname = 'io_scene_xray.remove_all_omfs'
    bl_label = 'Remove All OMF Files'
    bl_description = 'Remove all omf files'
    bl_options = {'UNDO'}

    def execute(self, context):
        context.scene.xray.merge_omf.omf_files.clear()
        utils.draw.redraw_areas()
        return {'FINISHED'}


class XRAY_OT_set_omf_file(bpy.types.Operator):
    bl_idname = 'io_scene_xray.set_omf_file'
    bl_label = 'Set OMF File'
    bl_description = 'Set OMF file path'
    bl_options = {'UNDO'}

    filename_ext = '.omf'
    filter_glob = bpy.props.StringProperty(
        default='*.omf',
        options={'HIDDEN'}
    )
    directory = bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'HIDDEN'}
    )
    filepath = bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE', 'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        return context.scene.xray.merge_omf.omf_files

    def execute(self, context):
        scn = context.scene
        merge_props = scn.xray.merge_omf
        omf = merge_props.omf_files[merge_props.omf_index]
        omf.file_path = self.filepath
        omf.file_name = os.path.basename(self.filepath)
        utils.draw.redraw_areas()
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_remove_all_omfs,
    XRAY_OT_set_omf_file
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
