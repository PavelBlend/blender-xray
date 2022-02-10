# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import utils
from .. import icons
from .. import log
from .. import contexts
from .. import ie_props
from .. import ui
from .. import version_utils


class ImportOmfContext(
        contexts.ImportAnimationContext, contexts.ImportAnimationOnlyContext
    ):
    def __init__(self):
        super().__init__()
        self.import_bone_parts = None


class ExportOmfContext(
        contexts.ExportAnimationOnlyContext,
        contexts.ExportAnimationContext
    ):
    def __init__(self):
        super().__init__()
        self.export_mode = None
        self.export_bone_parts = None
        self.high_quality = None
        self.need_motions = None
        self.need_bone_groups = None


op_text = 'Game Motion'
filename_ext = '.omf'

motion_props = {
    'flag': bpy.props.BoolProperty(name='Selected for Import', default=True),
    'name': bpy.props.StringProperty(name='Motion Name'),
    'length': bpy.props.IntProperty(name='Motion Length'),
}


class Motion(bpy.types.PropertyGroup):
    props = motion_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))


import_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.omf', options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE'}
    ),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    ),
    'import_motions': ie_props.PropObjectMotionsImport(),
    'import_bone_parts': ie_props.prop_import_bone_parts(),
    'motions': bpy.props.CollectionProperty(type=Motion, name='Motions Filter'),
    'add_actions_to_motion_list': ie_props.prop_skl_add_actions_to_motion_list()
}


class XRAY_OT_import_omf(
        ie_props.BaseOperator, bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.omf'
    bl_label = 'Import .omf'
    bl_description = 'Import X-Ray Game Motion (omf)'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = import_props

    __parsed_file_name = None

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        import_context = ImportOmfContext()
        for file in self.files:
            file_ext = os.path.splitext(file.name)[-1].lower()
            if file_ext == '.omf':
                omf_path = os.path.join(self.directory, file.name)
                import_context.bpy_arm_obj = context.object
                import_context.filepath = omf_path
                import_context.import_bone_parts = self.import_bone_parts
                import_context.import_motions = self.import_motions
                import_context.add_actions_to_motion_list = \
                    self.add_actions_to_motion_list
                if self.motions:
                    import_context.selected_names = {
                        motion.name
                        for motion in self.motions
                            if motion.flag
                    }
                try:
                    imp.import_file(import_context)
                except utils.AppError as err:
                    import_context.errors.append(err)
            else:
                self.report(
                    {'ERROR'},
                    'Format of "{}" not recognised'.format(file.name)
                )
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.import_motions = preferences.omf_import_motions
        self.import_bone_parts = preferences.import_bone_parts
        self.add_actions_to_motion_list = preferences.omf_add_actions_to_motion_list
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
        row = layout.row()
        row.active = self.import_motions
        row.prop(self, 'add_actions_to_motion_list')
        if not self.import_motions and not self.import_bone_parts:
            layout.label(text='Nothing was Imported!', icon='ERROR')
        if self.import_motions:
            motions = self._get_motions()
        else:
            motions = []
        count = 0
        text = 'Filter Motions'
        enabled = len(motions) > 1

        if enabled:
            text = 'Filter Motions: '
            count = len([motion for motion in motions if motion.flag])
            if count == len(motions):
                text += 'All ({})'.format(count)
            else:
                text += str(count)
        else:
            if len(motions) == 1:
                layout.label(text='OMF file contains one motion')

        if enabled:
            _, box = ui.collapsible.draw(
                layout,
                self.bl_idname,
                text,
                enabled=enabled,
                icon='FILTER' if count < 100 else 'ERROR',
                style='nobox',
            )

            if box:
                col = box.column(align=True)
                ui.motion_list.BaseSelectMotionsOp.set_motions_list(None)
                col.template_list(
                    'XRAY_UL_motions_list', '',
                    self, 'motions',
                    context.scene.xray.import_omf, 'motion_index',
                )
                row = col.row(align=True)
                ui.motion_list.BaseSelectMotionsOp.set_data(self)
                row.operator(ui.motion_list.XRAY_OT_select_motions.bl_idname, icon='CHECKBOX_HLT')
                row.operator(ui.motion_list.XRAY_OT_deselect_motions.bl_idname, icon='CHECKBOX_DEHLT')
                row.operator(ui.motion_list.XRAY_OT_deselect_duplicated_motions.bl_idname, icon='COPY_ID')

    def _get_motions(self):
        items = self.motions
        if len(self.files) == 1:
            file_path = os.path.join(self.directory, self.files[0].name)
            if file_path.lower().endswith('.omf'):
                if os.path.exists(file_path):
                    if self.__parsed_file_name != file_path:
                        file_data = utils.read_file(file_path)
                        motions_names = imp.examine_motions(file_data)
                        items.clear()
                        for name in motions_names:
                            items.add().name = name
                        self.__parsed_file_name = file_path
        else:
            items.clear()
        return items


export_props = {
    'filter_glob': bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'}),
    'export_mode': ie_props.prop_omf_export_mode(),
    'export_motions': ie_props.PropObjectMotionsExport(),
    'export_bone_parts': ie_props.prop_export_bone_parts(),
    'high_quality': ie_props.prop_omf_high_quality()
}


class XRAY_OT_export_omf(ie_props.BaseOperator, bpy_extras.io_utils.ExportHelper):
    bl_idname = 'xray_export.omf'
    bl_label = 'Export .omf'
    bl_description = 'Exports X-Ray skeletal game motions'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        layout.label(text='Export Mode:')
        layout.prop(self, 'export_mode', expand=True)
        layout.prop(self, 'high_quality')
        col = layout.column()
        col.active = not self.export_mode in ('OVERWRITE', 'ADD')
        col.prop(self, 'export_motions')
        col.prop(self, 'export_bone_parts')
        if self.export_mode == 'REPLACE':
            if not self.export_motions and not self.export_bone_parts:
                layout.label(text='Nothing was Exported!', icon='ERROR')

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        obj = context.object
        export_context = ExportOmfContext()
        export_context.bpy_arm_obj = obj
        export_context.filepath = self.filepath
        export_context.export_mode = self.export_mode
        export_context.export_motions = self.export_motions
        export_context.export_bone_parts = self.export_bone_parts
        export_context.high_quality = self.high_quality
        if self.export_mode in ('REPLACE', 'ADD'):
            if not os.path.exists(export_context.filepath):
                self.report(
                    {'ERROR'},
                    'File not found: "{}"'.format(export_context.filepath)
                )
                return {'CANCELLED'}
        if self.export_mode == 'REPLACE':
            if not self.export_motions and not self.export_bone_parts:
                self.report(
                    {'ERROR'},
                    'Nothing was exported. Change the export settings.'
                )
                return {'CANCELLED'}
        if self.export_mode in ('OVERWRITE', 'ADD'):
            need_motions = True
            if self.export_mode == 'OVERWRITE':
                need_bone_groups = True
            else:
                need_bone_groups = False
        else:
            if self.export_motions:
                need_motions = True
            else:
                need_motions = False
            if self.export_bone_parts:
                need_bone_groups = True
            else:
                need_bone_groups = False
        motions_count = len(obj.xray.motions_collection)
        bone_groups_count = len(obj.pose.bone_groups)
        if not motions_count and need_motions:
            self.report(
                {'ERROR'},
                'Armature object "{}" has no actions'.format(obj.name)
            )
            return {'CANCELLED'}
        if not bone_groups_count and need_bone_groups:
            self.report(
                {'ERROR'},
                'Armature object "{}" has no bone groups'.format(obj.name)
            )
            return {'CANCELLED'}
        export_context.need_motions = need_motions
        export_context.need_bone_groups = need_bone_groups
        try:
            exp.export_omf_file(export_context)
        except utils.AppError as err:
            export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.export_mode = preferences.omf_export_mode
        self.export_bone_parts = preferences.omf_export_bone_parts
        self.export_motions = preferences.omf_motions_export
        self.high_quality = preferences.omf_high_quality
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
        self.filepath = obj.name
        motions_count = len(obj.xray.motions_collection)
        bone_groups_count = len(obj.pose.bone_groups)
        if not motions_count and not bone_groups_count:
            self.report(
                {'ERROR'},
                'Armature object "{}" has no actions and bone groups'.format(
                    obj.name
                )
            )
            return {'CANCELLED'}
        if not self.filepath.lower().endswith(filename_ext):
            self.filepath += filename_ext
        return super().invoke(context, event)


classes = (
    Motion,
    XRAY_OT_import_omf,
    XRAY_OT_export_omf
)


def register():
    version_utils.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
