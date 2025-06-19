# blender modules
import bpy

# addon modules
from . import props
from .. import utils
from .. import formats


class XRAY_UL_path_presets_list(bpy.types.UIList):
    bl_idname = 'XRAY_UL_path_presets_list'

    def draw_item(
            self,
            context,
            layout,
            data,
            item,
            icon,
            active_data,
            active_propname,
            index
        ):

        if data.paths_presets_index == index:
            icon = 'CHECKBOX_HLT'
        else:
            icon = 'CHECKBOX_DEHLT'

        row = layout.row()
        row.label(text='', icon=icon)

        layout.prop(item, 'name', text='')


class XRAY_UL_path_configs_list(bpy.types.UIList):
    bl_idname = 'XRAY_UL_path_configs_list'

    def draw_item(
            self,
            context,
            layout,
            data,
            item,
            icon,
            active_data,
            active_propname,
            index
        ):

        if data.paths_configs_index == index:
            icon = 'CHECKBOX_HLT'
        else:
            icon = 'CHECKBOX_DEHLT'

        row = layout.row()
        row.label(text='', icon=icon)

        layout.prop(item, 'name', text='')


classes = (
    XRAY_UL_path_presets_list,
    XRAY_UL_path_configs_list
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
