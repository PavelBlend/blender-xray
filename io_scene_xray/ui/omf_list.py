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


classes = (
    XRAY_OT_remove_all_omfs,
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
