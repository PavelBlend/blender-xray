import re

import bpy

from .. import registry
from ..xray_motions import MOTIONS_FILTER_ALL


class BaseSelectMotionsOp(bpy.types.Operator):
    __ARGS__ = [None, None]

    @classmethod
    def set_motions_list(cls, mlist):
        cls.__ARGS__[0] = mlist

    @classmethod
    def set_data(cls, data):
        cls.__ARGS__[1] = data

    def execute(self, _context):
        mlist, data = self.__ARGS__
        name_filter = MOTIONS_FILTER_ALL
        if mlist and mlist.filter_name:
            rgx = re.compile('.*' + re.escape(mlist.filter_name).replace('\\*', '.*') + '.*')
            name_filter = lambda name: (rgx.match(name) is not None) ^ mlist.use_filter_invert
        for motion in data.motions:
            if name_filter(motion.name):
                self._update_motion(motion)
        return {'FINISHED'}

    def _update_motion(self, motion):
        pass


@registry.module_thing
class _SelectMotionsOp(BaseSelectMotionsOp):
    bl_idname = 'io_scene_xray.motions_select'
    bl_label = 'Select'
    bl_description = 'Select all displayed importing motions'

    def _update_motion(self, motion):
        motion.flag = True


@registry.module_thing
class _DeselectMotionsOp(BaseSelectMotionsOp):
    bl_idname = 'io_scene_xray.motions_deselect'
    bl_label = 'Deselect'
    bl_description = 'Deselect all displayed importing motions'

    def _update_motion(self, motion):
        motion.flag = False


@registry.module_thing
class _DeselectDuplicatedMotionsOp(BaseSelectMotionsOp):
    bl_idname = 'io_scene_xray.motions_deselect_duplicated'
    bl_label = 'Dups'
    bl_description = 'Deselect displayed importing motions which already exist in the scene'

    def _update_motion(self, motion):
        if bpy.data.actions.get(motion.name):
            motion.flag = False


@registry.module_thing
class XRAY_UL_MotionsList(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, _icon, _active_data, _active_propname):
        BaseSelectMotionsOp.set_motions_list(self)  # A dirty hack

        row = layout.row(align=True)
        row.prop(
            item, 'flag',
            icon='CHECKBOX_HLT' if item.flag else 'CHECKBOX_DEHLT',
            text='', emboss=False,
        )
        row.label(text=item.name)
