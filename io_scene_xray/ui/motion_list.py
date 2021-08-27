# standart modules
import re

# blender modules
import bpy

# addon modules
from .. import xray_motions


class BaseSelectMotionsOp(bpy.types.Operator):
    __ARGS__ = [None, None]

    @classmethod
    def set_motions_list(cls, mlist):
        cls.__ARGS__[0] = mlist

    @classmethod
    def set_data(cls, data):
        cls.__ARGS__[1] = data

    def execute(self, context):
        mlist, data = self.__ARGS__
        name_filter = xray_motions.MOTIONS_FILTER_ALL
        if mlist and mlist.filter_name:
            rgx = re.compile('.*' + re.escape(mlist.filter_name).replace('\\*', '.*') + '.*')
            name_filter = lambda name: (rgx.match(name) is not None) ^ mlist.use_filter_invert
        for motion in data.motions:
            if name_filter(motion.name):
                self._update_motion(motion)
        return {'FINISHED'}

    def _update_motion(self, motion):
        pass


class XRAY_OT_select_motions(BaseSelectMotionsOp):
    bl_idname = 'io_scene_xray.motions_select'
    bl_label = 'Select'
    bl_description = 'Select all displayed importing motions'

    def _update_motion(self, motion):
        motion.flag = True


class XRAY_OT_deselect_motions(BaseSelectMotionsOp):
    bl_idname = 'io_scene_xray.motions_deselect'
    bl_label = 'Deselect'
    bl_description = 'Deselect all displayed importing motions'

    def _update_motion(self, motion):
        motion.flag = False


class XRAY_OT_deselect_duplicated_motions(BaseSelectMotionsOp):
    bl_idname = 'io_scene_xray.motions_deselect_duplicated'
    bl_label = 'Dups'
    bl_description = 'Deselect displayed importing motions which already exist in the scene'

    def _update_motion(self, motion):
        if bpy.data.actions.get(motion.name):
            motion.flag = False


class XRAY_UL_motions_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        BaseSelectMotionsOp.set_motions_list(self)  # A dirty hack

        row = layout.row(align=True)
        row.prop(
            item, 'flag',
            icon='CHECKBOX_HLT' if item.flag else 'CHECKBOX_DEHLT',
            text='', emboss=False,
        )
        row.label(text=item.name)


classes = (
    XRAY_OT_select_motions,
    XRAY_OT_deselect_motions,
    XRAY_OT_deselect_duplicated_motions,
    XRAY_UL_motions_list
)


def register():
    for clas in classes:
        bpy.utils.register_class(clas)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
