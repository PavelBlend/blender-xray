# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import contexts
from .. import log
from .. import icons
from .. import utils
from .. import version_utils
from .. import plugin_props


class ImportBonesContext(contexts.ImportContext):
    def __init__(self):
        super().__init__()
        self.bpy_arm_obj = None
        self.import_bone_parts = None
        self.import_bone_properties = None


class ExportBonesContext(contexts.ExportAnimationOnlyContext):
    def __init__(self):
        super().__init__()
        self.export_bone_parts = None
        self.export_bone_properties = None


def menu_func_import(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_import_bones.bl_idname,
        text=utils.build_op_label(XRAY_OT_import_bones),
        icon_value=icon
    )


def menu_func_export(self, context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_bones.bl_idname,
        text=utils.build_op_label(XRAY_OT_export_bones),
        icon_value=icon
    )


BONES_EXT = '.bones'
op_text = 'Bones Data'

op_import_bones_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+BONES_EXT, options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE'}
    ),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    ),
    'import_bone_parts': plugin_props.prop_import_bone_parts(),
    'import_bone_properties': plugin_props.prop_import_bone_properties()
}


class XRAY_OT_import_bones(
        plugin_props.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.bones'
    bl_label = 'Import .bones'
    bl_description = 'Import X-Ray Bones Data'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    draw_fun = menu_func_import
    text = op_text
    ext = BONES_EXT
    filename_ext = BONES_EXT

    if not version_utils.IS_28:
        for prop_name, prop_value in op_import_bones_props.items():
            exec('{0} = op_import_bones_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        if len(self.files) > 1:
            self.report({'ERROR'}, 'Too many selected files. Select one file')
            return {'CANCELLED'}
        if not len(self.files):
            self.report({'ERROR'}, 'No file selected')
            return {'CANCELLED'}
        if not self.files[0].name:
            self.report({'ERROR'}, 'No file selected')
            return {'CANCELLED'}
        filename = self.files[0].name
        filepath = os.path.join(self.directory, filename)
        ext = os.path.splitext(filename)[-1].lower()
        if ext == '.bones':
            if not os.path.exists(filepath):
                self.report(
                    {'ERROR'},
                    'File not found: "{}"'.format(filepath)
                )
                return {'CANCELLED'}
            imp_props = self.import_bone_properties
            imp_parts = self.import_bone_parts
            if not imp_props and not imp_parts:
                self.report({'ERROR'}, 'Nothing is imported')
                return {'CANCELLED'}
            import_context = ImportBonesContext()
            import_context.import_bone_properties = imp_props
            import_context.import_bone_parts = imp_parts
            import_context.filepath = filepath
            import_context.bpy_arm_obj = context.object
            try:
                imp.import_file(import_context)
            except utils.AppError as err:
                import_context.errors.append(err)
        else:
            self.report(
                {'ERROR'},
                'Format of "{}" not recognised'.format(filepath)
            )
            return {'CANCELLED'}
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'import_bone_properties')
        layout.prop(self, 'import_bone_parts')
        if not self.import_bone_properties and not self.import_bone_parts:
            layout.label(text='Nothing is imported', icon='ERROR')

    def invoke(self, context, event):
        obj = context.object
        if not obj:
            self.report({'ERROR'}, 'There is no active object')
            return {'CANCELLED'}
        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, 'The active object is not an armature')
            return {'CANCELLED'}
        prefs = version_utils.get_preferences()
        # import bone parts
        self.import_bone_parts = prefs.bones_import_bone_parts
        # import bone properties
        self.import_bone_properties = prefs.bones_import_bone_properties
        return super().invoke(context, event)


op_export_bones_props = {
    'directory': bpy.props.StringProperty(subtype='FILE_PATH'),
    'filter_glob': bpy.props.StringProperty(
        default='*'+BONES_EXT,
        options={'HIDDEN'}
    ),
    'export_bone_properties': plugin_props.prop_export_bone_properties(),
    'export_bone_parts': plugin_props.prop_export_bone_parts()
}


class XRAY_OT_export_bones(plugin_props.BaseOperator):
    bl_idname = 'xray_export.bones'
    bl_label = 'Export .bones'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    draw_fun = menu_func_export
    text = op_text
    ext = BONES_EXT
    filename_ext = BONES_EXT

    objects_list = []

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_bones_props.items():
            exec('{0} = op_export_bones_props.get("{0}")'.format(prop_name))

    def get_objects(self, context):
        self.objects_list.clear()
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                self.objects_list.append(obj.name)

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        self.get_objects(context)
        for object_name in self.objects_list:
            filepath = os.path.join(self.directory, object_name)
            if not filepath.lower().endswith(self.filename_ext):
                filepath += self.filename_ext
            obj = context.scene.objects[object_name]
            try:
                exp_parts = self.export_bone_parts
                exp_props = self.export_bone_properties
                export_context = ExportBonesContext()
                export_context.bpy_arm_obj = obj
                export_context.filepath = filepath
                export_context.export_bone_parts = exp_parts
                export_context.export_bone_properties = exp_props
                exp.export_file(export_context)
            except utils.AppError as err:
                raise err
        self.objects_list.clear()
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'export_bone_properties')
        layout.prop(self, 'export_bone_parts')
        if not self.export_bone_properties and not self.export_bone_parts:
            layout.label(text='Nothing is exported', icon='ERROR')

    def invoke(self, context, event):
        selected_objects_count = len(context.selected_objects)
        if not selected_objects_count:
            self.report({'ERROR'}, 'There is no selected object')
            return {'CANCELLED'}
        self.get_objects(context)
        if not self.objects_list:
            self.report({'ERROR'}, 'No selected armatures')
            return {'CANCELLED'}
        if len(self.objects_list) == 1:
            return bpy.ops.xray_export.bone('INVOKE_DEFAULT')
        prefs = version_utils.get_preferences()
        # export bone parts
        self.export_bone_parts = prefs.bones_export_bone_parts
        # export bone properties
        self.export_bone_properties = prefs.bones_export_bone_properties
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


op_export_bone_props = {
    'directory': bpy.props.StringProperty(subtype='FILE_PATH'),
    'object_name': bpy.props.StringProperty(options={'HIDDEN'}),
    'filter_glob': bpy.props.StringProperty(
        default='*'+BONES_EXT,
        options={'HIDDEN'}
    ),
    'export_bone_properties': plugin_props.prop_export_bone_properties(),
    'export_bone_parts': plugin_props.prop_export_bone_parts()
}


class XRAY_OT_export_bone(
        plugin_props.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.bone'
    bl_label = 'Export .bones'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = BONES_EXT
    objects = []

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_bone_props.items():
            exec('{0} = op_export_bone_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        obj = context.scene.objects[self.object_name]
        try:
            export_context = ExportBonesContext()
            export_context.bpy_arm_obj = obj
            export_context.filepath = self.filepath
            export_context.export_bone_parts = self.export_bone_parts
            export_context.export_bone_properties = self.export_bone_properties
            exp.export_file(export_context)
        except utils.AppError as err:
            raise err
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'export_bone_properties')
        layout.prop(self, 'export_bone_parts')
        if not self.export_bone_properties and not self.export_bone_parts:
            layout.label(text='Nothing is exported', icon='ERROR')

    def invoke(self, context, event):
        selected_objects_count = len(context.selected_objects)
        if not selected_objects_count:
            self.report({'ERROR'}, 'There is no selected object')
            return {'CANCELLED'}
        self.objects.clear()
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                self.objects.append(obj.name)
        bpy_obj = bpy.data.objects[self.objects[0]]
        self.object_name = bpy_obj.name
        self.filepath = os.path.join(self.directory, self.object_name)
        if not self.filepath.lower().endswith(self.filename_ext):
            self.filepath += self.filename_ext
        prefs = version_utils.get_preferences()
        # export bone parts
        self.export_bone_parts = prefs.bones_export_bone_parts
        # export bone properties
        self.export_bone_properties = prefs.bones_export_bone_properties
        return super().invoke(context, event)


classes = (
    (XRAY_OT_import_bones, op_import_bones_props),
    (XRAY_OT_export_bones, op_export_bones_props),
    (XRAY_OT_export_bone, op_export_bone_props)
)


def register():
    for operator_class, operator_props in classes:
        version_utils.assign_props([(operator_props, operator_class), ])
        bpy.utils.register_class(operator_class)


def unregister():
    for operator_class, operator_props in reversed(classes):
        bpy.utils.unregister_class(operator_class)
