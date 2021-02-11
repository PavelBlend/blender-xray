import os

import bpy, bpy_extras

from . import imp, exp, props
from .. import plugin_prefs, registry, utils, plugin, context
from ..ui import collapsible
from ..skl import props as skl_props
from ..obj.imp import props as obj_imp_props
from ..obj.exp import props as obj_exp_props
from ..ui.motion_list import (
    BaseSelectMotionsOp,
    _SelectMotionsOp,
    _DeselectMotionsOp,
    _DeselectDuplicatedMotionsOp
)
from ..version_utils import IS_28, assign_props, get_multiply


class ImportOmfContext(
        context.ImportAnimationContext, context.ImportAnimationOnlyContext
    ):
    def __init__(self):
        context.ImportAnimationContext.__init__(self)
        context.ImportAnimationOnlyContext.__init__(self)
        self.import_bone_parts = None


class ExportOmfContext(
        context.ExportAnimationOnlyContext,
        context.ExportAnimationContext
    ):
    def __init__(self):
        context.ExportAnimationOnlyContext.__init__(self)
        context.ExportAnimationContext.__init__(self)
        self.export_mode = None
        self.export_bone_parts = None


motion_props = {
    'flag': bpy.props.BoolProperty(name='Selected for Import', default=True),
    'name': bpy.props.StringProperty(name='Motion Name'),
    'length': bpy.props.IntProperty(name='Motion Length'),
}


class Motion(bpy.types.PropertyGroup):
    if not IS_28:
        exec('{0} = motion_props.get("{0}")'.format('flag'))
        exec('{0} = motion_props.get("{0}")'.format('name'))


op_import_omf_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.omf', options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE'}
    ),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    ),
    'import_motions': obj_imp_props.PropObjectMotionsImport(),
    'import_bone_parts': props.prop_import_bone_parts(),
    'motions': bpy.props.CollectionProperty(type=Motion, name='Motions Filter'),
    'add_actions_to_motion_list': skl_props.prop_skl_add_actions_to_motion_list()
}


@registry.module_thing
@registry.requires(Motion)
class IMPORT_OT_xray_omf(
        bpy.types.Operator, bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.omf'
    bl_label = 'Import OMF'
    bl_description = 'Import X-Ray Game Motion (omf)'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    __parsed_file_name = None

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
                import_context = ImportOmfContext()
                import_context.bpy_arm_obj = context.object
                import_context.filepath = os.path.join(
                    self.directory, file.name
                )
                import_context.import_bone_parts = self.import_bone_parts
                import_context.import_motions = self.import_motions
                import_context.add_actions_to_motion_list = \
                    self.add_actions_to_motion_list
                if self.motions:
                    import_context.selected_names = set(
                        m.name for m in self.motions if m.flag
                    )
                try:
                    imp.import_file(import_context)
                except utils.AppError as err:
                    self.report({'ERROR'}, str(err))
                    return {'CANCELLED'}
            else:
                self.report(
                    {'ERROR'}, 'Format of {} not recognised'.format(file)
                )
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
        self.import_motions = prefs.object_motions_import
        self.import_bone_parts = prefs.import_bone_parts
        self.add_actions_to_motion_list = prefs.add_actions_to_motion_list
        obj = context.object
        if not obj:
            self.report({'ERROR'}, 'No active object')
            return {'CANCELLED'}
        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, 'Active object "{}" is not armature'.format(obj.name))
            return {'CANCELLED'}
        return super().invoke(context, event)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'import_motions')
        layout.prop(self, 'import_bone_parts')
        if not self.import_motions:
            return
        row = layout.row()
        row.active = self.import_motions
        row.prop(self, 'add_actions_to_motion_list')
        motions = self._get_motions()
        count = 0
        text = 'Filter Motions'
        enabled = len(motions) > 1

        if enabled:
            text = 'Filter Motions: '
            count = len([m for m in motions if m.flag])
            if count == len(motions):
                text += 'All ({})'.format(count)
            else:
                text += str(count)
        else:
            if len(motions) == 1:
                layout.label(text='OMF file contains one motion')

        _, box = collapsible.draw(
            layout,
            self.bl_idname,
            text,
            enabled=enabled,
            icon='FILTER' if count < 100 else 'ERROR',
            style='nobox',
        )

        if box:
            col = box.column(align=True)
            BaseSelectMotionsOp.set_motions_list(None)
            col.template_list(
                'XRAY_UL_MotionsList', '',
                self, 'motions',
                context.scene.xray.import_omf, 'motion_index',
            )
            row = col.row(align=True)
            BaseSelectMotionsOp.set_data(self)
            row.operator(_SelectMotionsOp.bl_idname, icon='CHECKBOX_HLT')
            row.operator(_DeselectMotionsOp.bl_idname, icon='CHECKBOX_DEHLT')
            row.operator(_DeselectDuplicatedMotionsOp.bl_idname, icon='COPY_ID')

    def _get_motions(self):
        items = self.motions
        if len(self.files) == 1:
            fpath = os.path.join(self.directory, self.files[0].name)
            if fpath.lower().endswith('.omf'):
                if os.path.exists(fpath):
                    if self.__parsed_file_name != fpath:
                        with open(fpath, 'rb') as file:
                            motions_names = imp.examine_motions(file.read())
                        items.clear()
                        for name in motions_names:
                            items.add().name = name
                        self.__parsed_file_name = fpath
        else:
            items.clear()
        return items


filename_ext = '.omf'
op_export_omf_props = {
    'filter_glob': bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'}),
    'export_mode': props.prop_omf_export_mode(),
    'export_motions': obj_exp_props.PropObjectMotionsExport(),
    'export_bone_parts': props.prop_export_bone_parts()
}


@registry.module_thing
class EXPORT_OT_xray_omf(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = 'xray_export.omf'
    bl_label = 'Export .omf'
    bl_description = 'Exports X-Ray skeletal game motions'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = '.omf'

    if not IS_28:
        for prop_name, prop_value in op_export_omf_props.items():
            exec('{0} = op_export_omf_props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        row = layout.split(factor=0.5)
        row.label(text='Export Mode:')
        row.prop(self, 'export_mode', text='')
        row = layout.row()
        row.active = not self.export_mode in ('OVERWRITE', 'ADD')
        row.prop(self, 'export_motions')
        row = layout.row()
        row.active = not self.export_mode in ('OVERWRITE', 'ADD')
        row.prop(self, 'export_bone_parts')

    @utils.set_cursor_state
    def execute(self, context):
        export_context = ExportOmfContext()
        export_context.bpy_arm_obj = context.object
        export_context.filepath = self.filepath
        export_context.export_mode = self.export_mode
        export_context.export_motions = self.export_motions
        export_context.export_bone_parts = self.export_bone_parts
        try:
            exp.export_omf_file(export_context)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
        self.export_mode = prefs.omf_export_mode
        self.export_bone_parts = prefs.omf_export_bone_parts
        self.export_motions = prefs.object_motions_export
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
    (motion_props, Motion),
    (op_import_omf_props, IMPORT_OT_xray_omf),
    (op_export_omf_props, EXPORT_OT_xray_omf)
])


def menu_func_import(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        IMPORT_OT_xray_omf.bl_idname,
        text='X-Ray Game Motion (.omf)',
        icon_value=icon
    )


def menu_func_export(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        EXPORT_OT_xray_omf.bl_idname,
        text='X-Ray Game Motion (.omf)',
        icon_value=icon
    )
