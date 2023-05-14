# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import ie
from .. import contexts
from ... import utils
from ... import text
from ... import log


class ImportLevelContext(contexts.ImportMeshContext):
    pass


op_text = 'Game Level'
file_name_text = 'level'
if utils.version.broken_file_browser_filter():
    file_filter_import = '*'
    file_filter_export = '*'
else:
    file_filter_import = 'level'
    file_filter_export = 'level;level.geom;level.geomx;level.cform'


import_props = {
    'filter_glob': bpy.props.StringProperty(
        default=file_filter_import, options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'HIDDEN'}
    ),
    'filepath': bpy.props.StringProperty(
        subtype="FILE_PATH", options={'SKIP_SAVE', 'HIDDEN'}
    ),
    'processed': bpy.props.BoolProperty(default=False, options={'HIDDEN'})
}


class XRAY_OT_import_level(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):

    bl_idname = 'xray_import.level'
    bl_label = 'Import level'
    bl_description = 'Import X-Ray Game Level (level)'
    bl_options = {'REGISTER', 'UNDO'}

    text = op_text
    filename_ext = ''
    ext = file_name_text
    props = import_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'levels_folder')

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, 'No file selected')
            return {'CANCELLED'}
        import_context = ImportLevelContext()
        import_context.operator=self
        import_context.filepath = self.filepath
        try:
            imp.import_file(import_context)
        except log.AppError as err:
            import_context.errors.append(err)
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        return super().invoke(context, event)


def get_level_objs(objs, level_objs):
    for obj in objs:

        if not obj:
            continue

        if not obj.xray.is_level:
            continue

        if obj.xray.level.object_type != 'LEVEL':
            continue

        level_objs.add(obj)


def get_export_objs(context):
    level_objs = set()
    active_obj = context.active_object

    get_level_objs((active_obj, *context.selected_objects), level_objs)

    if not level_objs:
        if active_obj:
            level_objs.add(active_obj)

    if not level_objs:
        get_level_objs(bpy.data.objects, level_objs)

        if len(level_objs) > 1:
            level_objs.clear()

    if not level_objs:
        level_objs.add(active_obj)

    return list(level_objs)


export_props = {
    'directory': bpy.props.StringProperty(
        subtype='DIR_PATH', options={'HIDDEN'}
    ),
    'filter_glob': bpy.props.StringProperty(
        default=file_filter_export,
        options={'HIDDEN'}
    ),
    'processed': bpy.props.BoolProperty(default=False, options={'HIDDEN'})
}


class XRAY_OT_export_level(utils.ie.BaseOperator):
    bl_idname = 'xray_export.level'
    bl_label = 'Export level'

    text = op_text
    filename_ext = ''
    ext = file_name_text
    props = export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):    # pragma: no cover
        utils.ie.open_imp_exp_folder(self, 'levels_folder')

    def export(self, level_object, context):
        exp.export_file(level_object, self.directory)
        return {'FINISHED'}

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        level_objs = get_export_objs(context)
        return self.export(level_objs[0], context)

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        level_objs = get_export_objs(context)

        if len(level_objs) > 1:
            self.report(
                {'ERROR'},
                'Too many selected level-objects'
            )
            return {'CANCELLED'}

        level_object = level_objs[0]

        if not level_object:
            self.report(
                {'ERROR'},
                text.get_text(text.error.no_active_obj)
            )
            return {'CANCELLED'}

        if not level_object.xray.is_level:
            self.report(
                {'ERROR'},
                'Object "{}" does not have level parameter enabled.'.format(
                    level_object.name
                )
            )
            return {'CANCELLED'}

        if level_object.xray.level.object_type != 'LEVEL':
            self.report(
                {'ERROR'},
                'Object "{0}" has an invalid type: {1}. Must be "Level".'.format(
                    level_object.name,
                    level_object.xray.level.object_type
                )
            )
            return {'CANCELLED'}

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_import_level,
    XRAY_OT_export_level
)


def register():
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
