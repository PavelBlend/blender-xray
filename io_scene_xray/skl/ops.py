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
from .. import plugin_props
from .. import ui
from .. import utils
from .. import xray_motions
from .. import version_utils


def menu_func_import(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_import_skls.bl_idname,
        text=utils.build_op_label(XRAY_OT_import_skls),
        icon_value=icon
    )


def menu_func_export(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_skls.bl_idname,
        text=utils.build_op_label(XRAY_OT_export_skls),
        icon_value=icon
    )


op_text = 'Skeletal Animation'
filename_ext = '.skls'

motion_props = {
    'flag': bpy.props.BoolProperty(name='Selected for Import', default=True),
    'name': bpy.props.StringProperty(name='Motion Name')
}


class Motion(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        exec('{0} = motion_props.get("{0}")'.format('flag'))
        exec('{0} = motion_props.get("{0}")'.format('name'))


op_import_skls_props = {
    'filter_glob': bpy.props.StringProperty(default='*.skl;*.skls', options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'files': bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement),
    'motions': bpy.props.CollectionProperty(type=Motion, name='Motions Filter'),
    'use_motion_prefix_name': plugin_props.PropObjectUseMotionPrefixName(),
    'add_actions_to_motion_list': plugin_props.prop_skl_add_actions_to_motion_list()
}


class XRAY_OT_import_skls(plugin_props.BaseOperator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'xray_import.skls'
    bl_label = 'Import .skl/.skls'
    bl_description = 'Imports X-Ray skeletal amination'
    bl_options = {'UNDO', 'PRESET'}

    draw_fun = menu_func_import
    text = op_text
    ext = '.skl/.skls'
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_import_skls_props.items():
            exec('{0} = op_import_skls_props.get("{0}")'.format(prop_name))

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
            if os.path.exists(fpath):
                with open(fpath, 'rb') as file:
                    return xray_motions.examine_motions(file.read())
        return tuple()

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        motions_filter = xray_motions.MOTIONS_FILTER_ALL
        if self.motions:
            selected_names = set(m.name for m in self.motions if m.flag)
            motions_filter = lambda name: name in selected_names
        import_context = imp.ImportSklContext()
        import_context.bpy_arm_obj = context.active_object
        import_context.motions_filter = motions_filter
        import_context.use_motion_prefix_name = self.use_motion_prefix_name
        import_context.filename = None
        import_context.add_actions_to_motion_list = self.add_actions_to_motion_list
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            fpath = os.path.join(self.directory, file.name)
            import_context.filename = file.name
            try:
                if ext == '.skl':
                    imp.import_skl_file(fpath, import_context)
                elif ext == '.skls':
                    imp.import_skls_file(fpath, import_context)
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
        self.use_motion_prefix_name = preferences.skls_use_motion_prefix_name
        self.add_actions_to_motion_list = preferences.add_actions_to_motion_list
        return super().invoke(context, event)


filename_ext = '.skl'
op_export_skl_props = {
    'filter_glob': bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'}),
}


class XRAY_OT_export_skl(plugin_props.BaseOperator, bpy_extras.io_utils.ExportHelper):
    bl_idname = 'xray_export.skl'
    bl_label = 'Export .skl'
    bl_description = 'Exports X-Ray skeletal animation'
    bl_options = {'UNDO'}

    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_skl_props.items():
            exec('{0} = op_export_skl_props.get("{0}")'.format(prop_name))

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
op_export_skls_props = {
    'filter_glob': bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'}),
}


class XRAY_OT_export_skls(plugin_props.BaseOperator, utils.FilenameExtHelper):
    bl_idname = 'xray_export.skls'
    bl_label = 'Export .skls'
    bl_description = 'Exports X-Ray skeletal animation'
    bl_options = {'UNDO'}

    draw_fun = menu_func_export
    text = op_text
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_skls_props.items():
            exec('{0} = op_export_skls_props.get("{0}")'.format(prop_name))

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


classes = (
    (Motion, motion_props),
    (XRAY_OT_import_skls, op_import_skls_props),
    (XRAY_OT_export_skl, op_export_skl_props),
    (XRAY_OT_export_skls, op_export_skls_props)
)


def register():
    for operator, props in classes:
        version_utils.assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
