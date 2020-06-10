import os

import bpy, bpy_extras

from . import imp
from . import exp
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


filename_ext = '.omf'
op_export_omf_props = {
    'filter_glob': bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'}),
}


@registry.module_thing
class EXPORT_OT_xray_omf(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = 'xray_export.omf'
    bl_label = 'Export .omf'
    bl_description = 'Exports X-Ray skeletal game motions'

    filename_ext = '.omf'

    if not IS_28:
        for prop_name, prop_value in op_export_omf_props.items():
            exec('{0} = op_export_omf_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.object
        try:
            exp.export_omf_file(self.filepath, obj)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        if len(context.selected_objects) > 1:
            self.report({'ERROR'}, 'Too many selected objects')
            return {'CANCELLED'}
        if not len(context.selected_objects):
            self.report({'ERROR'}, 'No selected objects')
            return {'CANCELLED'}
        obj = context.object
        if not obj:
            self.report({'ERROR'}, 'No active object')
            return {'CANCELLED'}
        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, 'Active object "{}" is not armature'.format(obj.name))
            return {'CANCELLED'}
        if not len(obj.xray.motions_collection):
            self.report({'ERROR'}, 'Armature object "{}" has no actions'.format(obj.name))
            return {'CANCELLED'}
        if not len(obj.pose.bone_groups):
            self.report({'ERROR'}, 'Armature object "{}" has no bone groups'.format(obj.name))
            return {'CANCELLED'}
        if not self.filepath.lower().endswith(filename_ext):
            self.filepath += filename_ext
        return super().invoke(context, event)


assign_props([
    (op_import_omf_props, IMPORT_OT_xray_omf),
    (op_export_omf_props, EXPORT_OT_xray_omf)
])


def menu_func_import(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        IMPORT_OT_xray_omf.bl_idname,
        text='Game Motion (.omf)',
        icon_value=icon
    )


def menu_func_export(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        EXPORT_OT_xray_omf.bl_idname,
        text='Game Motion (.omf)',
        icon_value=icon
    )
