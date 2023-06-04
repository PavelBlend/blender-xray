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
from ... import text
from ... import rw
from ... import ui


OP_TEXT = 'Game Motion'
OMF_EXT = '.omf'


class ImportOmfContext(
        contexts.ImportAnimationContext,
        contexts.ImportAnimationOnlyContext
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
    # file browser properties
    'filter_glob': bpy.props.StringProperty(
        default='*.omf',
        options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH",
        options={'SKIP_SAVE'}
    ),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    ),

    # import properties
    'import_motions': ie.PropObjectMotionsImport(),
    'import_bone_parts': ie.prop_import_bone_parts(),
    'add_to_motion_list': ie.prop_skl_add_actions_to_motion_list(),
    'motions': bpy.props.CollectionProperty(
        type=Motion,
        name='Motions Filter'
    ),

    # system properties
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

    text = OP_TEXT
    ext = OMF_EXT
    filename_ext = OMF_EXT
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

        has_sel = utils.ie.has_selected_files(self)
        if not has_sel:
            return {'CANCELLED'}

        # import context
        imp_ctx = ImportOmfContext()

        imp_ctx.bpy_arm_obj = context.active_object
        imp_ctx.import_bone_parts = self.import_bone_parts
        imp_ctx.import_motions = self.import_motions
        imp_ctx.add_to_motion_list = self.add_to_motion_list

        for file in self.files:
            imp_ctx.filepath = os.path.join(self.directory, file.name)

            # search selected motions
            if self.motions:
                imp_ctx.selected_names = {
                    motion.name
                    for motion in self.motions
                        if motion.flag
                }

            # import
            try:
                imp.import_file(imp_ctx)
            except log.AppError as err:
                imp_ctx.errors.append(err)

        # report errors
        for err in imp_ctx.errors:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        # set default settings
        pref = utils.version.get_preferences()
        self.import_motions = pref.omf_import_motions
        self.import_bone_parts = pref.import_bone_parts
        self.add_to_motion_list = pref.omf_add_actions_to_motion_list

        # verify object
        obj = context.active_object

        if not obj:
            self.report({'ERROR'}, text.get_text(text.error.no_active_obj))
            return {'CANCELLED'}

        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, text.get_text(text.error.is_not_arm))
            return {'CANCELLED'}

        return super().invoke(context, event)

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'meshes_folder')

        layout = self.layout

        layout.prop(self, 'import_motions')
        layout.prop(self, 'import_bone_parts')

        row = layout.row()
        row.active = self.import_motions
        row.prop(self, 'add_to_motion_list')

        if not self.import_motions and not self.import_bone_parts:
            layout.label(
                text=text.get_text(text.error.omf_nothing_imp),
                icon='ERROR'
            )

        if self.import_motions:
            self._update_motions_list()
            motions = self.motions
        else:
            motions = []

        count = 0
        label = 'Filter Motions'
        enabled = len(motions) > 1

        if enabled:
            label = 'Filter Motions: '
            count = len([motion for motion in motions if motion.flag])
            if count == len(motions):
                label += 'All ({})'.format(count)
            else:
                label += str(count)

        else:
            if len(motions) == 1:
                layout.label(text='OMF file contains one motion')

        if enabled:
            _, box = ui.collapsible.draw(
                layout,
                self.bl_idname,
                label,
                enabled=enabled,
                icon='FILTER' if count < 100 else 'ERROR',
                style='nobox',
            )

            # motion list
            if box:
                col = box.column(align=True)
                ui.motion_list.BaseSelectMotionsOp.set_motions_list(None)
                col.template_list(
                    'XRAY_UL_motions_list',
                    '',
                    self,
                    'motions',
                    context.scene.xray.import_omf,
                    'motion_index'
                )
                row = col.row(align=True)
                ui.motion_list.BaseSelectMotionsOp.set_data(self)

                # select/deselect operators
                row.operator(
                    ui.motion_list.XRAY_OT_select_motions.bl_idname,
                    icon='CHECKBOX_HLT'
                )
                row.operator(
                    ui.motion_list.XRAY_OT_deselect_motions.bl_idname,
                    icon='CHECKBOX_DEHLT'
                )
                row.operator(
                    ui.motion_list.XRAY_OT_deselect_dupli_motions.bl_idname,
                    icon='COPY_ID'
                )

    def _update_motions_list(self):
        if len(self.files) == 1:
            file_path = os.path.join(self.directory, self.files[0].name)

            if os.path.exists(file_path):
                if self.__parsed_file_name != file_path:

                    self.__parsed_file_name = file_path
                    self.motions.clear()
                    file_data = rw.utils.read_file(file_path)
                    motions_names = imp.examine_motions(file_data)

                    for name in motions_names:
                        self.motions.add().name = name

        else:
            self.motions.clear()


export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+OMF_EXT,
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

    text = OP_TEXT
    ext = OMF_EXT
    filename_ext = OMF_EXT
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
        self.filepath = utils.ie.add_file_ext(self.obj.name, OMF_EXT)
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
        default='*'+OMF_EXT,
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

    text = OP_TEXT
    ext = OMF_EXT
    filename_ext = OMF_EXT
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
            name = utils.ie.add_file_ext(obj.name, OMF_EXT)
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
