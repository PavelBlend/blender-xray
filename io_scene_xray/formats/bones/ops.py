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
from ... import log
from ... import utils


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


BONES_EXT = '.bones'
op_text = 'Bones Data'


class XRAY_OT_import_bones(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ImportHelper
    ):
    bl_idname = 'xray_import.bones'
    bl_label = 'Import .bones'
    bl_description = 'Import X-Ray Bones Data'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = BONES_EXT
    filename_ext = BONES_EXT

    filter_glob = bpy.props.StringProperty(
        default='*'+BONES_EXT,
        options={'HIDDEN'}
    )
    directory = bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'SKIP_SAVE'}
    )
    files = bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    )
    import_bone_parts = ie.prop_import_bone_parts()
    import_bone_properties = ie.prop_import_bone_properties()
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Import *.bones')

        if len(self.files) > 1:
            self.report({'ERROR'}, 'Too many selected files. Select one file')
            return {'CANCELLED'}
        if not self.files or (len(self.files) == 1 and not self.files[0].name):
            self.report({'ERROR'}, 'No file selected!')
            return {'CANCELLED'}
        filename = self.files[0].name
        filepath = os.path.join(self.directory, filename)
        file_ext = os.path.splitext(filename)[-1].lower()
        imp_props = self.import_bone_properties
        imp_parts = self.import_bone_parts
        if not imp_props and not imp_parts:
            self.report({'ERROR'}, 'Nothing is imported')
            return {'CANCELLED'}
        import_context = ImportBonesContext()
        import_context.import_bone_properties = imp_props
        import_context.import_bone_parts = imp_parts
        import_context.filepath = filepath
        import_context.bpy_arm_obj = context.active_object
        try:
            imp.import_file(import_context)
        except log.AppError as err:
            import_context.errors.append(err)
        for err in import_context.errors:
            log.err(err)
        return {'FINISHED'}

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        layout.prop(self, 'import_bone_properties')
        layout.prop(self, 'import_bone_parts')
        if not self.import_bone_properties and not self.import_bone_parts:
            layout.label(text='Nothing is imported', icon='ERROR')

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, 'There is no active object')
            return {'CANCELLED'}
        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, 'The active object is not an armature')
            return {'CANCELLED'}
        prefs = utils.version.get_preferences()
        # import bone parts
        self.import_bone_parts = prefs.bones_import_bone_parts
        # import bone properties
        self.import_bone_properties = prefs.bones_import_bone_properties
        return super().invoke(context, event)


class XRAY_OT_export_bones(utils.ie.BaseOperator):
    bl_idname = 'xray_export.bones'
    bl_label = 'Export .bones'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = BONES_EXT
    filename_ext = BONES_EXT

    directory = bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob = bpy.props.StringProperty(
        default='*'+BONES_EXT,
        options={'HIDDEN'}
    )
    export_bone_properties = ie.prop_export_bone_properties()
    export_bone_parts = ie.prop_export_bone_parts()
    processed = bpy.props.BoolProperty(default=False, options={'HIDDEN'})

    objects_list = []

    def get_objects(self, context):
        self.objects_list.clear()
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                self.objects_list.append(obj.name)

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.bones')

        self.get_objects(context)
        export_context = ExportBonesContext()
        for object_name in self.objects_list:
            filepath = os.path.join(self.directory, object_name)
            filepath = utils.ie.add_file_ext(filepath, self.filename_ext)
            obj = context.scene.objects[object_name]
            try:
                exp_parts = self.export_bone_parts
                exp_props = self.export_bone_properties
                export_context.bpy_arm_obj = obj
                export_context.filepath = filepath
                export_context.export_bone_parts = exp_parts
                export_context.export_bone_properties = exp_props
                exp.export_file(export_context)
            except log.AppError as err:
                export_context.errors.append(err)
        self.objects_list.clear()
        for err in export_context.errors:
            log.err(err)
        return {'FINISHED'}

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        layout.prop(self, 'export_bone_properties')
        layout.prop(self, 'export_bone_parts')
        if not self.export_bone_properties and not self.export_bone_parts:
            layout.label(text='Nothing is exported', icon='ERROR')

    @utils.ie.run_imp_exp_operator
    def invoke(self, context, event):    # pragma: no cover
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

        pref = utils.version.get_preferences()

        self.export_bone_parts = pref.bones_export_bone_parts
        self.export_bone_properties = pref.bones_export_bone_properties

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


class XRAY_OT_export_bone(
        utils.ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):

    bl_idname = 'xray_export.bone'
    bl_label = 'Export .bones'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = BONES_EXT
    objects = []

    directory = bpy.props.StringProperty(subtype='FILE_PATH')
    object_name = bpy.props.StringProperty(options={'HIDDEN'})
    filter_glob = bpy.props.StringProperty(
        default='*'+BONES_EXT,
        options={'HIDDEN'}
    )
    export_bone_properties = ie.prop_export_bone_properties()
    export_bone_parts = ie.prop_export_bone_parts()

    @log.execute_with_logger
    @utils.stats.execute_with_stats
    @utils.ie.set_initial_state
    def execute(self, context):
        utils.stats.update('Export *.bones')

        obj = context.scene.objects[self.object_name]
        try:
            export_context = ExportBonesContext()
            export_context.bpy_arm_obj = obj
            export_context.filepath = self.filepath
            export_context.export_bone_parts = self.export_bone_parts
            export_context.export_bone_properties = self.export_bone_properties
            exp.export_file(export_context)
        except log.AppError as err:
            export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        return {'FINISHED'}

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        layout.prop(self, 'export_bone_properties')
        layout.prop(self, 'export_bone_parts')
        if not self.export_bone_properties and not self.export_bone_parts:
            layout.label(text='Nothing is exported', icon='ERROR')

    def invoke(self, context, event):    # pragma: no cover
        selected_objects_count = len(context.selected_objects)

        if not selected_objects_count:
            self.report({'ERROR'}, 'There is no selected object')
            return {'CANCELLED'}

        self.objects.clear()
        for bpy_obj in context.selected_objects:
            if bpy_obj.type == 'ARMATURE':
                self.objects.append(bpy_obj.name)

        obj = bpy.data.objects[self.objects[0]]

        self.object_name = obj.name
        file_name = utils.ie.add_file_ext(obj.name, self.filename_ext)
        self.filepath = os.path.join(self.directory, file_name)

        pref = utils.version.get_preferences()

        self.export_bone_parts = pref.bones_export_bone_parts
        self.export_bone_properties = pref.bones_export_bone_properties

        return super().invoke(context, event)


classes = (
    XRAY_OT_import_bones,
    XRAY_OT_export_bones,
    XRAY_OT_export_bone
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator_class in reversed(classes):
        bpy.utils.unregister_class(operator_class)
