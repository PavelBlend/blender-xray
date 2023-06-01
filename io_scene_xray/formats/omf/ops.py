# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import ie
from .. import contexts
from ... import utils
from ... import log
from ... import rw
from ... import ui


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

    if not utils.version.IS_28:
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
    'import_motions': ie.PropObjectMotionsImport(),
    'import_bone_parts': ie.prop_import_bone_parts(),
    'motions': bpy.props.CollectionProperty(type=Motion, name='Motions Filter'),
    'add_actions_to_motion_list': ie.prop_skl_add_actions_to_motion_list(),
    'processed': bpy.props.BoolProperty(default=False, options={'HIDDEN'})
}


class XRAY_OT_import_omf(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
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

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Import *.omf')

        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}
        import_context = ImportOmfContext()
        for file in self.files:
            file_ext = os.path.splitext(file.name)[-1].lower()
            omf_path = os.path.join(self.directory, file.name)
            import_context.bpy_arm_obj = context.active_object
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
            except log.AppError as err:
                import_context.errors.append(err)
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        preferences = utils.version.get_preferences()
        self.import_motions = preferences.omf_import_motions
        self.import_bone_parts = preferences.import_bone_parts
        self.add_actions_to_motion_list = preferences.omf_add_actions_to_motion_list
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, 'No active object')
            return {'CANCELLED'}
        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, 'Active object "{}" is not armature'.format(obj.name))
            return {'CANCELLED'}
        return super().invoke(context, event)

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'meshes_folder')
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
                        file_data = rw.utils.read_file(file_path)
                        motions_names = imp.examine_motions(file_data)
                        items.clear()
                        for name in motions_names:
                            items.add().name = name
                        self.__parsed_file_name = file_path
        else:
            items.clear()
        return items


export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'export_mode': ie.prop_omf_export_mode(),
    'export_motions': ie.PropObjectMotionsExport(),
    'export_bone_parts': ie.prop_export_bone_parts(),
    'high_quality': ie.prop_omf_high_quality(),
    'processed': bpy.props.BoolProperty(default=False, options={'HIDDEN'})
}


class XRAY_OT_export_omf_file(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.omf_file'
    bl_label = 'Export .omf'
    bl_description = 'Exports X-Ray skeletal game motions'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props
    obj = None

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'meshes_folder')
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

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.omf')

        active_object = context.active_object
        if self.obj:
            utils.version.set_active_object(self.obj)
        else:
            self.obj = active_object
        export_context = ExportOmfContext()
        export_context.bpy_arm_obj = self.obj
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
        motions_count = len(self.obj.xray.motions_collection)
        bone_groups_count = len(self.obj.pose.bone_groups)
        if not motions_count and need_motions:
            self.report(
                {'ERROR'},
                'Armature object "{}" has no actions'.format(self.obj.name)
            )
            return {'CANCELLED'}
        if not bone_groups_count and need_bone_groups:
            self.report(
                {'ERROR'},
                'Armature object "{}" has no bone groups'.format(self.obj.name)
            )
            return {'CANCELLED'}
        export_context.need_motions = need_motions
        export_context.need_bone_groups = need_bone_groups
        try:
            exp.export_omf_file(export_context)
        except log.AppError as err:
            export_context.errors.append(err)
        utils.version.set_active_object(active_object)
        for err in export_context.errors:
            log.err(err)
        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        preferences = utils.version.get_preferences()
        self.export_mode = preferences.omf_export_mode
        self.export_bone_parts = preferences.omf_export_bone_parts
        self.export_motions = preferences.omf_motions_export
        self.high_quality = preferences.omf_high_quality
        sel_objs_count = len(context.selected_objects)
        objs = [
            obj
            for obj in context.selected_objects
                if obj.type == 'ARMATURE'
        ]
        arm_count = len(objs)
        if arm_count > 1:
            self.report({'ERROR'}, 'Too many selected armature-objects')
            return {'CANCELLED'}
        if not arm_count and sel_objs_count:
            self.report(
                {'ERROR'},
                'There are no armatures among the selected objects'
            )
            return {'CANCELLED'}
        if not sel_objs_count and not arm_count:
            self.report({'ERROR'}, 'No selected objects')
            return {'CANCELLED'}
        self.obj = objs[0]
        self.filepath = utils.ie.add_file_ext(self.obj.name, filename_ext)
        motions_count = len(self.obj.xray.motions_collection)
        bone_groups_count = len(self.obj.pose.bone_groups)
        if not motions_count and not bone_groups_count:
            self.report(
                {'ERROR'},
                'Armature object "{}" has no actions and bone groups'.format(
                    self.obj.name
                )
            )
            return {'CANCELLED'}
        return super().invoke(context, event)


def get_arm_objs(operator, context):
    sel_objs_count = len(context.selected_objects)
    objs = [
        obj
        for obj in context.selected_objects
            if obj.type == 'ARMATURE'
    ]
    arm_count = len(objs)
    
    if not arm_count and sel_objs_count:
        operator.report(
            {'ERROR'},
            'There are no armatures among the selected objects'
        )
        return
    
    if not arm_count and not sel_objs_count:
        operator.report({'ERROR'}, 'No selected objects')
        return

    return objs


export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype='FILE_PATH'),
    'export_motions': ie.PropObjectMotionsExport(),
    'export_bone_parts': ie.prop_export_bone_parts(),
    'high_quality': ie.prop_omf_high_quality(),
    'processed': bpy.props.BoolProperty(default=False, options={'HIDDEN'})
}


class XRAY_OT_export_omf(utils.ie.BaseOperator):
    bl_idname = 'xray_export.omf'
    bl_label = 'Export .omf'
    bl_description = 'Exports X-Ray skeletal game motions'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'meshes_folder')

        layout = self.layout

        layout.prop(self, 'high_quality')

        if not self.export_motions and not self.export_bone_parts:
            layout.label(text='Nothing was Exported!', icon='ERROR')

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @log.with_context('export-omf')
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.omf')

        arm_objs = get_arm_objs(self, context)
        if not arm_objs:
            return {'CANCELLED'}

        export_context = ExportOmfContext()

        export_context.high_quality = self.high_quality
        export_context.need_motions = True
        export_context.need_bone_groups = True

        for obj in arm_objs:
            name = utils.ie.add_file_ext(obj.name, filename_ext)
            filepath = os.path.join(self.directory, name)

            skip = False

            motions_count = len(obj.xray.motions_collection)
            try:
                if not motions_count:
                    raise log.AppError(
                        'Armature object has no motions',
                        log.props(object=obj.name)
                    )
            except log.AppError as err:
                log.err(err)
                skip = True

            bone_groups_count = len(obj.pose.bone_groups)
            try:
                if not bone_groups_count:
                    raise log.AppError(
                        'Armature object has no bone groups',
                        log.props(object=obj.name)
                    )
            except log.AppError as err:
                log.err(err)
                skip = True

            if skip:
                continue

            export_context.bpy_arm_obj = obj
            export_context.filepath = filepath

            try:
                exp.export_omf_file(export_context)
            except log.AppError as err:
                export_context.errors.append(err)

        for err in export_context.errors:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        pref = utils.version.get_preferences()

        self.high_quality = pref.omf_high_quality

        arm_objs = get_arm_objs(self, context)
        if not arm_objs:
            return {'CANCELLED'}

        if len(arm_objs) == 1:
            return bpy.ops.xray_export.omf_file('INVOKE_DEFAULT')

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


classes = (
    Motion,
    XRAY_OT_import_omf,
    XRAY_OT_export_omf,
    XRAY_OT_export_omf_file
)


def register():
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
