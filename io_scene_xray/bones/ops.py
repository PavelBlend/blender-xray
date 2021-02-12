# standart modules
import os

# blender modules
import bpy
from bpy_extras import io_utils

# addon modules
from .. import plugin, plugin_prefs, registry
from ..utils import execute_with_logger, set_cursor_state, AppError
from ..version_utils import assign_props, IS_28
from ..omf import props as omf_props
from . import imp, props, exp


class ImportBonesContext:
    def __init__(self):
        self.import_bone_parts = None
        self.import_bone_properties = None


BONES_EXT = '.bones'
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
    'import_bone_parts': omf_props.prop_import_bone_parts(),
    'import_bone_properties': props.prop_import_bone_properties()
}


@registry.module_thing
class IMPORT_OT_xray_bones(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = 'xray_import.bones'
    bl_label = 'Import .bones'
    bl_description = 'Import X-Ray Bones Data'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = BONES_EXT

    if not IS_28:
        for prop_name, prop_value in op_import_bones_props.items():
            exec('{0} = op_import_bones_props.get("{0}")'.format(prop_name))

    @execute_with_logger
    @set_cursor_state
    def execute(self, _context):
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
                self.report({'ERROR'}, 'File not found: "{}"'.format(filepath))
                return {'CANCELLED'}
            try:
                if not self.import_bone_properties and not self.import_bone_parts:
                    self.report({'ERROR'}, 'Nothing is imported')
                    return {'CANCELLED'}
                import_context = ImportBonesContext()
                import_context.import_bone_properties = self.import_bone_properties
                import_context.import_bone_parts = self.import_bone_parts
                imp.import_file(filepath, import_context)
                return {'FINISHED'}
            except AppError as err:
                self.report({'ERROR'}, str(err))
                return {'CANCELLED'}
        else:
            self.report(
                {'ERROR'}, 'Format of "{}" not recognised'.format(filepath)
            )
            return {'CANCELLED'}

    def draw(self, _context):
        layout = self.layout
        layout.prop(self, 'import_bone_properties')
        layout.prop(self, 'import_bone_parts')
        if not self.import_bone_properties and not self.import_bone_parts:
            layout.label(text='Nothing is imported', icon='ERROR')

    def invoke(self, context, event):
        obj = bpy.context.object
        if not obj:
            self.report({'ERROR'}, 'There is no active object')
            return {'CANCELLED'}
        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, 'The active object is not an armature')
            return {'CANCELLED'}
        prefs = plugin_prefs.get_preferences()
        # import bone parts
        self.import_bone_parts = prefs.bones_import_bone_parts
        # import bone properties
        self.import_bone_properties = prefs.bones_import_bone_properties
        return super().invoke(context, event)


op_export_bones_props = {
    'directory': bpy.props.StringProperty(subtype='FILE_PATH'),
    'object_name': bpy.props.StringProperty(options={'HIDDEN'}),
    'filter_glob': bpy.props.StringProperty(
        default='*'+BONES_EXT,
        options={'HIDDEN'}
    )
}


@registry.module_thing
class EXPORT_OT_xray_bones(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = 'xray_export.bones'
    bl_label = 'Export .bones'

    filename_ext = BONES_EXT

    if not IS_28:
        for prop_name, prop_value in op_export_bones_props.items():
            exec('{0} = op_export_bones_props.get("{0}")'.format(prop_name))

    @execute_with_logger
    @set_cursor_state
    def execute(self, context):
        obj = context.scene.objects[self.object_name]
        try:
            exp.export_file(obj, self.filepath)
        except AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        selected_objects_count = len(context.selected_objects)
        if not selected_objects_count:
            self.report({'ERROR'}, 'There is no selected object')
            return {'CANCELLED'}
        if selected_objects_count > 1:
            self.report(
                {'ERROR'},
                'Many objects are selected. One object needs to be selected'
            )
            return {'CANCELLED'}
        bpy_obj = context.selected_objects[0]
        if bpy_obj.type != 'ARMATURE':
            self.report({'ERROR'}, 'The exported object is not a armature')
            return {'CANCELLED'}
        self.object_name = bpy_obj.name
        self.filepath = os.path.join(self.directory, self.object_name)
        if not self.filepath.lower().endswith(self.filename_ext):
            self.filepath += self.filename_ext
        return super().invoke(context, event)


assign_props([
    (op_import_bones_props, IMPORT_OT_xray_bones),
    (op_export_bones_props, EXPORT_OT_xray_bones),
])


def menu_func_import(self, _context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        IMPORT_OT_xray_bones.bl_idname,
        text='X-Ray Bones Data (.bones)', icon_value=icon
    )


def menu_func_export(self, _context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        EXPORT_OT_xray_bones.bl_idname,
        text='X-Ray Bones Data (.bones)', icon_value=icon
    )
