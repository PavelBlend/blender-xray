import os, time

import bpy, bpy_extras

from . import imp
from .. import plugin_prefs, registry, utils, plugin
from ..version_utils import IS_28, assign_props


op_import_omf_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.omf', options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE'}
    ),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    )
}


@registry.module_thing
class IMPORT_OT_xray_omf(
        bpy.types.Operator, bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.omf'
    bl_label = 'Import OMF'
    bl_description = 'Import X-Ray Game Motion (omf)'
    bl_options = {'REGISTER', 'UNDO'}

    if not IS_28:
        for prop_name, prop_value in op_import_omf_props.items():
            exec('{0} = op_import_omf_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):
        st = time.time()
        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            if ext == '.omf':
                imp.import_file(
                    os.path.join(self.directory, file.name), context.object
                )
            else:
                self.report(
                    {'ERROR'}, 'Format of {} not recognised'.format(file)
                )
        print(time.time() - st)
        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.object
        if not obj:
            self.report({'ERROR'}, 'No active object')
            return {'CANCELLED'}
        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, 'Active object "{}" is not armature'.format(obj.name))
            return {'CANCELLED'}
        return super().invoke(context, event)


assign_props([
    (op_import_omf_props, IMPORT_OT_xray_omf),
])


def menu_func_import(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        IMPORT_OT_xray_omf.bl_idname,
        text='Game Motion (.omf)',
        icon_value=icon
    )
