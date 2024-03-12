# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import ie
from .. import motions
from ... import log
from ... import ui
from ... import rw
from ... import utils
from ... import text


op_text = 'Skeletal Animations'
filename_ext = '.skls'
skls_ext = '.skls'
skl_ext = '.skl'


class Motion(bpy.types.PropertyGroup):
    flag = bpy.props.BoolProperty(name='Selected for Import', default=True)
    name = bpy.props.StringProperty(name='Motion Name')


def get_arm_obj():
    arm_obj = None
    active = bpy.context.active_object

    # get armature-object by active object
    if active and active.type == 'ARMATURE':
        arm_obj = active

    if not arm_obj:

        # get armature-object by selected objects
        arm_objs = []
        for obj in bpy.context.selected_objects:
            if obj.type == 'ARMATURE':
                arm_objs.append(obj)

        if len(arm_objs) == 1:
            arm_obj = arm_objs[0]

    return arm_obj


class XRAY_OT_import_skls(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.skls'
    bl_label = 'Import .skl/.skls'
    bl_description = 'Imports X-Ray skeletal amination'
    bl_options = {'UNDO', 'PRESET'}

    text = op_text
    ext = '.skl/.skls'
    filename_ext = skls_ext

    # file browser properties
    filter_glob = bpy.props.StringProperty(
        default='*.skl;*.skls',
        options={'HIDDEN'}
    )
    directory = bpy.props.StringProperty(subtype='DIR_PATH')
    files = bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    )

    # import properties
    motions = bpy.props.CollectionProperty(
        type=Motion,
        name='Motions Filter'
    )
    motion_index = bpy.props.IntProperty(options={'HIDDEN'})
    add_to_motion_list = ie.prop_skl_add_actions_to_motion_list()

    # system properties
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    __parsed_file_name = None

    def draw(self, context):    # pragma: no cover
        layout = self.layout

        utils.draw.draw_files_count(self)

        layout.prop(self, 'add_to_motion_list')

        motions_list, count = self._get_motions(), 0
        label = 'Filter Motions'
        enabled = len(motions_list) > 1

        if enabled:
            label = 'Filter Motions: '
            count = len([motion for motion in motions_list if motion.flag])
            if count == len(motions_list):
                label += 'All ({})'.format(count)
            else:
                label += str(count)
        _, box = ui.collapsible.draw(
            layout,
            self.bl_idname,
            label,
            enabled=enabled,
            icon='FILTER' if count < 100 else 'ERROR',
            style='nobox',
        )

        if box:
            col = box.column(align=True)
            ui.motion_filter.BaseSelectMotionsOp.set_motions_list(None)
            col.template_list(
                'XRAY_UL_motions_list',
                '',
                self,
                'motions',
                self,
                'motion_index'
            )
            row = col.row(align=True)
            ui.motion_filter.BaseSelectMotionsOp.set_data(self)
            row.operator(
                ui.motion_filter.XRAY_OT_select_motions.bl_idname,
                icon='CHECKBOX_HLT'
            )
            row.operator(
                ui.motion_filter.XRAY_OT_deselect_motions.bl_idname,
                icon='CHECKBOX_DEHLT'
            )
            row.operator(
                ui.motion_filter.XRAY_OT_deselect_dupli_motions.bl_idname,
                icon='COPY_ID'
            )

    def _get_motions(self):
        items = self.motions

        if len(self.files) == 1:
            file_path = os.path.join(self.directory, self.files[0].name)
            if self.__parsed_file_name != file_path:
                items.clear()
                for name in self._examine_file(file_path):
                    items.add().name = name
                self.__parsed_file_name = file_path

        else:
            items.clear()

        return items

    @staticmethod
    def _examine_file(file_path):
        if file_path.lower().endswith(skls_ext):
            if os.path.exists(file_path):
                file_data = rw.utils.read_file(file_path)
                return motions.imp.examine_motions(file_data)

        return tuple()

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Import *.skl/*skls')

        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}

        motions_filter = motions.imp.MOTIONS_FILTER_ALL
        if self.motions:
            selected_names = {
                motion.name
                for motion in self.motions
                    if motion.flag
            }
            motions_filter = lambda name: name in selected_names

        obj = get_arm_obj()

        import_context = imp.ImportSklContext()

        import_context.bpy_arm_obj = obj
        import_context.motions_filter = motions_filter
        import_context.filename = None
        import_context.add_to_motion_list = self.add_to_motion_list

        for file in self.files:
            file_ext = os.path.splitext(file.name)[-1].lower()
            file_path = os.path.join(self.directory, file.name)
            import_context.filename = file.name

            try:
                if file_ext == skl_ext:
                    imp.import_skl_file(file_path, import_context)
                elif file_ext == skls_ext:
                    imp.import_skls_file(file_path, import_context)
                else:
                    try:
                        imp.import_skl_file(file_path, import_context)
                    except:
                        imp.import_skls_file(file_path, import_context)

            except log.AppError as err:
                import_context.errors.append(err)

        for err in import_context.errors:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    @utils.ie.invoke_require_armature
    def invoke(self, context, event):    # pragma: no cover
        pref = utils.version.get_preferences()

        self.add_to_motion_list = pref.add_to_motion_list

        return super().invoke(context, event)


class XRAY_OT_export_skl(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):

    bl_idname = 'xray_export.skl'
    bl_label = 'Export .skl'
    bl_description = 'Exports X-Ray skeletal animation'
    bl_options = {'UNDO'}

    filename_ext = skl_ext

    filter_glob = bpy.props.StringProperty(
        default='*'+skl_ext,
        options={'HIDDEN'}
    )
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    action = None

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.execute_require_filepath
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.skl')

        export_context = exp.ExportSklsContext()
        export_context.bpy_arm_obj = get_arm_obj()
        export_context.action = self.action

        try:
            exp.export_skl_file(self.filepath, export_context)
        except log.AppError as err:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    @utils.ie.invoke_require_armature
    def invoke(self, context, event):    # pragma: no cover
        action_prop_name = XRAY_OT_export_skl.bl_idname + '.action'
        self.action = getattr(context, action_prop_name, None)

        if not action:
            return {'CANCELLED'}

        self.filepath = self.action.name

        if not self.filepath.lower().endswith(skl_ext):
            self.filepath += skl_ext

        return super().invoke(context, event)


class XRAY_OT_export_skls_file(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.skls_file'
    bl_label = 'Export .skls'
    bl_description = 'Exports X-Ray skeletal animation'
    bl_options = {'UNDO'}

    text = op_text
    ext = skls_ext
    filename_ext = skls_ext

    filter_glob = bpy.props.StringProperty(
        default='*'+skls_ext,
        options={'HIDDEN'}
    )

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.execute_require_filepath
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.skls')

        export_context = exp.ExportSklsContext()
        export_context.bpy_arm_obj = get_arm_obj()

        if not self.filepath.lower().endswith(skls_ext):
            self.filepath += skls_ext

        try:
            exp.export_skls_file(self.filepath, export_context, self.actions)
        except log.AppError as err:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.invoke_require_armature
    def invoke(self, context, event):    # pragma: no cover
        obj = get_arm_obj()

        if obj:
            self.filepath = utils.ie.add_file_ext(obj.name, self.filename_ext)
        else:
            self.report({'ERROR'}, text.error.no_active_obj)
            return {'CANCELLED'}

        self.actions = []
        for motion in obj.xray.motions_collection:
            action = bpy.data.actions.get(motion.name)
            if action:
                self.actions.append(action)

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


op_text = 'Skeletal Animations'


class XRAY_OT_export_skls(utils.ie.BaseOperator):
    bl_idname = 'xray_export.skls'
    bl_label = 'Export .skls'
    bl_description = 'Exports X-Ray skeletal animations'
    bl_options = {'UNDO'}

    text = op_text
    ext = skls_ext
    filename_ext = skls_ext

    directory = bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'HIDDEN'}
    )
    filter_glob = bpy.props.StringProperty(
        default='*' + skls_ext,
        options={'HIDDEN'}
    )
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.skls')

        export_context = exp.ExportSklsContext()
        exp_actions_count = 0
        objects = []

        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                objects.append(obj)

        for obj in objects:
            export_context.bpy_arm_obj = obj
            # file path
            file_name = obj.name
            file_name = utils.ie.add_file_ext(obj.name, skls_ext)
            filepath = os.path.join(self.directory, file_name)
            # collect actions
            actions = []

            for motion in obj.xray.motions_collection:
                action = bpy.data.actions.get(motion.name)
                if action:
                    actions.append(action)

            # export
            try:
                exp.export_skls_file(filepath, export_context, actions)
                exp_actions_count += len(actions)

            except log.AppError as err:
                export_context.errors.append(err)

        if not exp_actions_count:
            self.report({'WARNING'}, 'Selected objects have no actions')

        for err in export_context.errors:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        active = context.active_object

        if not context.selected_objects:
            if active and active.type == 'ARMATURE':
                return bpy.ops.xray_export.skls_file('INVOKE_DEFAULT')
            else:
                self.report({'ERROR'}, text.error.no_selected_obj)
                return {'CANCELLED'}

        if len(context.selected_objects) == 1:
            obj = context.selected_objects[0]
            if obj.type != 'ARMATURE':
                self.report({'ERROR'}, text.error.is_not_arm)
                return {'CANCELLED'}

            actions = []
            for motion in obj.xray.motions_collection:
                action = bpy.data.actions.get(motion.name)
                if action:
                    actions.append(action)

            if not actions:
                self.report({'ERROR'}, 'Active object has no animations')
                return {'CANCELLED'}

            return bpy.ops.xray_export.skls_file('INVOKE_DEFAULT')

        else:
            arm_objs = []
            for obj in context.selected_objects:
                if obj.type == 'ARMATURE':
                    arm_objs.append(obj)

            if not arm_objs:
                self.report({'ERROR'}, text.error.no_arm_obj)
                return {'CANCELLED'}

            if len(arm_objs) == 1:
                return bpy.ops.xray_export.skls_file('INVOKE_DEFAULT')

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


op_text = 'Skeletal Animation'


class XRAY_OT_export_skl_batch(utils.ie.BaseOperator):
    bl_idname = 'xray_export.skl_batch'
    bl_label = 'Export .skl'
    bl_description = 'Exports X-Ray skeletal animations'
    bl_options = {'UNDO'}

    text = op_text
    ext = skl_ext
    filename_ext = skl_ext

    directory = bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'HIDDEN'}
    )
    filter_glob = bpy.props.StringProperty(
        default='*'+skl_ext,
        options={'HIDDEN'}
    )
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    @log.execute_with_logger
    @log.with_context('export-skl-batch')
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.skl')

        export_context = exp.ExportSklsContext()
        exp_actions_count = 0
        objects = []

        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                objects.append(obj)

        use_sub_dirs = len(objects) > 1
        path_conflicts = []

        for obj in objects:
            export_context.bpy_arm_obj = obj
            sub_dir_name = obj.name
            directory = os.path.join(self.directory, sub_dir_name)

            if os.path.exists(directory) and os.path.isfile(directory):
                path_conflicts.append(directory)
                continue

            for motion in obj.xray.motions_collection:

                action = bpy.data.actions.get(motion.name)
                if not action:
                    continue

                export_context.action = action

                # skl file name
                file_name = action.name

                if obj.xray.use_custom_motion_names and motion.export_name:
                    file_name = motion.export_name

                if not file_name.lower().endswith(skl_ext):
                    file_name += skl_ext

                if use_sub_dirs:
                    filepath = os.path.join(directory, file_name)

                    if not os.path.exists(directory):
                        os.makedirs(directory)

                else:
                    filepath = os.path.join(self.directory, file_name)

                # export
                try:
                    exp.export_skl_file(filepath, export_context)
                    exp_actions_count += 1

                except log.AppError as err:
                    export_context.errors.append(err)

        # report errors
        if not exp_actions_count and not path_conflicts:
            self.report({'WARNING'}, 'Selected objects have no actions')

        for path in path_conflicts:
            err = log.AppError(
                text.error.skl_path_conflict,
                log.props(path=path)
            )
            log.err(err)

        for err in export_context.errors:
            log.err(err)

        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover

        if not context.selected_objects:
            self.report({'ERROR'}, 'No selected objects')
            return {'CANCELLED'}

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


classes = (
    Motion,
    XRAY_OT_import_skls,
    XRAY_OT_export_skl,
    XRAY_OT_export_skls,
    XRAY_OT_export_skls_file,
    XRAY_OT_export_skl_batch
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
