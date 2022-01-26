# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import icons
from .. import log
from .. import ie_props
from .. import ui
from .. import utils
from .. import xray_motions
from .. import draw_utils
from .. import version_utils


op_text = 'Skeletal Animations'
filename_ext = '.skls'

motion_props = {
    'flag': bpy.props.BoolProperty(name='Selected for Import', default=True),
    'name': bpy.props.StringProperty(name='Motion Name')
}


class Motion(bpy.types.PropertyGroup):
    props = motion_props

    if not version_utils.IS_28:
        exec('{0} = props.get("{0}")'.format('flag'))
        exec('{0} = props.get("{0}")'.format('name'))


import_props = {
    'filter_glob': bpy.props.StringProperty(default='*.skl;*.skls', options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'files': bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement),
    'motions': bpy.props.CollectionProperty(type=Motion, name='Motions Filter'),
    'add_actions_to_motion_list': ie_props.prop_skl_add_actions_to_motion_list()
}


class XRAY_OT_import_skls(ie_props.BaseOperator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'xray_import.skls'
    bl_label = 'Import .skl/.skls'
    bl_description = 'Imports X-Ray skeletal amination'
    bl_options = {'UNDO', 'PRESET'}

    text = op_text
    ext = '.skl/.skls'
    filename_ext = filename_ext
    props = import_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    __parsed_file_name = None

    def draw(self, context):
        layout = self.layout

        draw_utils.draw_files_count(self)

        layout.prop(self, 'add_actions_to_motion_list')

        motions, count = self._get_motions(), 0
        text = 'Filter Motions'
        enabled = len(motions) > 1
        if enabled:
            text = 'Filter Motions: '
            count = len([motion for motion in motions if motion.flag])
            if count == len(motions):
                text += 'All (%d)' % count
            else:
                text += str(count)
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
                context.scene.xray.import_skls, 'motion_index',
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
        if file_path.lower().endswith('.skls'):
            if os.path.exists(file_path):
                file_data = utils.read_file(file_path)
                return xray_motions.examine_motions(file_data)
        return tuple()

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        motions_filter = xray_motions.MOTIONS_FILTER_ALL
        if self.motions:
            selected_names = {
                motion.name
                for motion in self.motions
                    if motion.flag
            }
            motions_filter = lambda name: name in selected_names
        import_context = imp.ImportSklContext()
        import_context.bpy_arm_obj = context.active_object
        import_context.motions_filter = motions_filter
        import_context.filename = None
        import_context.add_actions_to_motion_list = self.add_actions_to_motion_list
        for file in self.files:
            file_ext = os.path.splitext(file.name)[-1].lower()
            file_path = os.path.join(self.directory, file.name)
            import_context.filename = file.name
            try:
                if file_ext == '.skl':
                    imp.import_skl_file(file_path, import_context)
                elif file_ext == '.skls':
                    imp.import_skls_file(file_path, import_context)
                else:
                    self.report({'ERROR'}, 'Format of {} not recognised'.format(file))
            except utils.AppError as err:
                import_context.errors.append(err)
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    @utils.invoke_require_armature
    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.add_actions_to_motion_list = preferences.add_actions_to_motion_list
        return super().invoke(context, event)


filename_ext = '.skl'
export_props = {
    'filter_glob': bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'}),
}


class XRAY_OT_export_skl(ie_props.BaseOperator, bpy_extras.io_utils.ExportHelper):
    bl_idname = 'xray_export.skl'
    bl_label = 'Export .skl'
    bl_description = 'Exports X-Ray skeletal animation'
    bl_options = {'UNDO'}

    filename_ext = filename_ext
    props = export_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    action = None

    @utils.execute_with_logger
    @utils.execute_require_filepath
    @utils.set_cursor_state
    def execute(self, context):
        export_context = exp.ExportSklsContext()
        export_context.bpy_arm_obj = context.active_object
        export_context.action = self.action
        try:
            exp.export_skl_file(self.filepath, export_context)
        except utils.AppError as err:
            log.err(err)
        return {'FINISHED'}

    @utils.invoke_require_armature
    def invoke(self, context, event):
        self.action = getattr(context, XRAY_OT_export_skl.bl_idname + '.action', None)
        assert self.action
        self.filepath = self.action.name
        if not self.filepath.lower().endswith(filename_ext):
            self.filepath += filename_ext
        return super().invoke(context, event)


filename_ext = '.skls'
export_props = {
    'filter_glob': bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'}),
}


class XRAY_OT_export_skls(ie_props.BaseOperator, utils.FilenameExtHelper):
    bl_idname = 'xray_export.skls'
    bl_label = 'Export .skls'
    bl_description = 'Exports X-Ray skeletal animation'
    bl_options = {'UNDO'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def export(self, context):
        export_context = exp.ExportSklsContext()
        export_context.bpy_arm_obj = context.active_object
        try:
            exp.export_skls_file(self.filepath, export_context, self.actions)
        except utils.AppError as err:
            log.err(err)

    @utils.invoke_require_armature
    def invoke(self, context, event):
        self.actions = []
        for motion in bpy.context.object.xray.motions_collection:
            action = bpy.data.actions.get(motion.name)
            if action:
                self.actions.append(action)
        if not self.actions:
            self.report({'ERROR'}, 'Active object has no animations')
            return {'CANCELLED'}
        return super().invoke(context, event)


filename_ext = '.skl'
op_text = 'Skeletal Animation'
export_props = {
    'directory': bpy.props.StringProperty(subtype="FILE_PATH"),
    'filter_glob': bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'}),
}


class XRAY_OT_export_skl_batch(ie_props.BaseOperator):
    bl_idname = 'xray_export.skl_batch'
    bl_label = 'Export .skl'
    bl_description = 'Exports X-Ray skeletal animations'
    bl_options = {'UNDO'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        export_context = exp.ExportSklsContext()
        exp_actions_count = 0
        objects = []
        for obj in context.selected_objects:
            if obj.type != 'ARMATURE':
                continue
            objects.append(obj)
        use_sub_dirs = len(objects) > 1
        for obj in objects:
            export_context.bpy_arm_obj = obj
            for motion in obj.xray.motions_collection:
                action = bpy.data.actions.get(motion.name)
                if not action:
                    continue
                export_context.action = action
                file_name = action.name
                if not file_name.lower().endswith(filename_ext):
                    file_name += filename_ext
                if use_sub_dirs:
                    sub_dir_name = obj.name
                    directory = os.path.join(self.directory, sub_dir_name)
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    filepath = os.path.join(directory, file_name)
                else:
                    filepath = os.path.join(self.directory, file_name)
                try:
                    exp.export_skl_file(filepath, export_context)
                    exp_actions_count += 1
                except utils.AppError as err:
                    export_context.errors.append(err)
        if not exp_actions_count:
            self.report({'WARNING'}, 'Selected objects have no actions')
        for err in export_context.errors:
            log.err(err)
        return {'FINISHED'}

    def invoke(self, context, event):
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
    XRAY_OT_export_skl_batch
)


def register():
    version_utils.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
