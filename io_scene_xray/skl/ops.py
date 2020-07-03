import os

import bpy
from bpy_extras import io_utils

from .. import registry, plugin_prefs
from ..ui import collapsible
from ..ui.motion_list import (
    BaseSelectMotionsOp,
    _SelectMotionsOp,
    _DeselectMotionsOp,
    _DeselectDuplicatedMotionsOp,
    XRAY_UL_MotionsList
)
from ..ops import BaseOperator as TestReadyOperator
from ..utils import (
    execute_with_logger, invoke_require_armature, execute_require_filepath,
    FilenameExtHelper, set_cursor_state
)
from ..xray_motions import MOTIONS_FILTER_ALL
from ..version_utils import assign_props, IS_28
from . import props
from ..obj.imp import props as obj_imp_props


motion_props = {
    'flag': bpy.props.BoolProperty(name='Selected for Import', default=True),
    'name': bpy.props.StringProperty(name='Motion Name')
}


class Motion(bpy.types.PropertyGroup):
    if not IS_28:
        exec('{0} = motion_props.get("{0}")'.format('flag'))
        exec('{0} = motion_props.get("{0}")'.format('name'))


op_import_skl_props = {
    'filter_glob': bpy.props.StringProperty(default='*.skl;*.skls', options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'files': bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement),
    'motions': bpy.props.CollectionProperty(type=Motion, name='Motions Filter'),
    'use_motion_prefix_name': obj_imp_props.PropObjectUseMotionPrefixName(),
    'add_actions_to_motion_list': props.prop_skl_add_actions_to_motion_list()
}


@registry.module_thing
@registry.requires(Motion)
class OpImportSkl(TestReadyOperator, io_utils.ImportHelper):
    bl_idname = 'xray_import.skl'
    bl_label = 'Import .skl/.skls'
    bl_description = 'Imports X-Ray skeletal amination'
    bl_options = {'UNDO', 'PRESET'}

    if not IS_28:
        for prop_name, prop_value in op_import_skl_props.items():
            exec('{0} = op_import_skl_props.get("{0}")'.format(prop_name))

    __parsed_file_name = None

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'use_motion_prefix_name')
        layout.prop(self, 'add_actions_to_motion_list')
        row = layout.row()
        row.enabled = False
        row.label(text='%d items' % len(self.files))

        motions, count = self._get_motions(), 0
        text = 'Filter Motions'
        enabled = len(motions) > 1
        if enabled:
            text = 'Filter Motions: '
            count = len([m for m in motions if m.flag])
            if count == len(motions):
                text += 'All (%d)' % count
            else:
                text += str(count)
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
                context.scene.xray.import_skls, 'motion_index',
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
            if self.__parsed_file_name != fpath:
                items.clear()
                for name in self._examine_file(fpath):
                    items.add().name = name
                self.__parsed_file_name = fpath
        else:
            items.clear()
        return items

    @staticmethod
    def _examine_file(fpath):
        if fpath.lower().endswith('.skls'):
            from ..xray_motions import examine_motions
            if os.path.exists(fpath):
                with open(fpath, 'rb') as file:
                    return examine_motions(file.read())
        return tuple()

    @execute_with_logger
    @set_cursor_state
    def execute(self, context):
        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        from .imp import import_skl_file, import_skls_file, ImportSklContext
        motions_filter = MOTIONS_FILTER_ALL
        if self.motions:
            selected_names = set(m.name for m in self.motions if m.flag)
            motions_filter = lambda name: name in selected_names
        import_context = ImportSklContext()
        import_context.bpy_arm_obj = context.active_object
        import_context.motions_filter = motions_filter
        import_context.use_motion_prefix_name = self.use_motion_prefix_name
        import_context.filename = None
        import_context.add_actions_to_motion_list = self.add_actions_to_motion_list
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            fpath = os.path.join(self.directory, file.name)
            import_context.filename = file.name
            if ext == '.skl':
                import_skl_file(fpath, import_context)
            elif ext == '.skls':
                import_skls_file(fpath, import_context)
            else:
                self.report({'ERROR'}, 'Format of {} not recognised'.format(file))
        return {'FINISHED'}

    @invoke_require_armature
    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
        self.use_motion_prefix_name = prefs.use_motion_prefix_name
        self.add_actions_to_motion_list = prefs.add_actions_to_motion_list
        return super().invoke(context, event)


filename_ext = '.skl'
op_export_skl_props = {
    'filter_glob': bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'}),
}


@registry.module_thing
class OpExportSkl(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = 'xray_export.skl'
    bl_label = 'Export .skl'
    bl_description = 'Exports X-Ray skeletal animation'
    bl_options = {'UNDO'}

    filename_ext = '.skl'

    if not IS_28:
        for prop_name, prop_value in op_export_skl_props.items():
            exec('{0} = op_export_skl_props.get("{0}")'.format(prop_name))

    action = None

    @execute_with_logger
    @execute_require_filepath
    @set_cursor_state
    def execute(self, context):
        from .exp import export_skl_file, ExportSklsContext
        export_context = ExportSklsContext()
        export_context.bpy_arm_obj = context.active_object
        export_context.action = self.action
        export_skl_file(self.filepath, export_context)
        return {'FINISHED'}

    @invoke_require_armature
    def invoke(self, context, event):
        self.action = getattr(context, OpExportSkl.bl_idname + '.action', None)
        assert self.action
        self.filepath = self.action.name
        if not self.filepath.lower().endswith(filename_ext):
            self.filepath += filename_ext
        return super().invoke(context, event)


filename_ext = '.skls'
op_export_skls_props = {
    'filter_glob': bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'}),
}


@registry.module_thing
class OpExportSkls(bpy.types.Operator, FilenameExtHelper):
    bl_idname = 'xray_export.skls'
    bl_label = 'Export .skls'
    bl_description = 'Exports X-Ray skeletal animation'
    bl_options = {'UNDO'}

    filename_ext = '.skls'

    if not IS_28:
        for prop_name, prop_value in op_export_skls_props.items():
            exec('{0} = op_export_skls_props.get("{0}")'.format(prop_name))

    def export(self, context):
        from .exp import export_skls_file, ExportSklsContext
        export_context = ExportSklsContext()
        export_context.bpy_arm_obj = context.active_object
        export_skls_file(self.filepath, export_context)

    @invoke_require_armature
    def invoke(self, context, event):
        return super().invoke(context, event)


assign_props([
    (motion_props, Motion),
    (op_import_skl_props, OpImportSkl),
    (op_export_skl_props, OpExportSkl),
    (op_export_skls_props, OpExportSkls)
])
