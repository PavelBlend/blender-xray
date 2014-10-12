import bpy
from bpy_extras import io_utils
from .xray_inject import inject_init, inject_done
from .utils import AppError


#noinspection PyUnusedLocal
class OpImportObject(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = 'xray_import.object'
    bl_label = 'Import .object'
    bl_description = 'Imports X-Ray object'
    bl_options = {'UNDO'}

    filter_glob = bpy.props.StringProperty(default='*.object', options={'HIDDEN'})

    directory = bpy.props.StringProperty(subtype="DIR_PATH")
    files = bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)

    shaped_bones = bpy.props.BoolProperty(
        name='custom shapes for bones',
        description='use custom shapes for imported bones'
    )

    def execute(self, context):
        addon_prefs = context.user_preferences.addons['io_scene_xray'].preferences
        textures_folder = addon_prefs.get_textures_folder()
        if not textures_folder:
            self.report({'ERROR'}, 'No textures folder specified')
            return {'CANCELLED'}
        if len(self.files) == 0:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        from .fmt_object_imp import import_file, ImportContext
        cx = ImportContext(
            report=self.report,
            textures=textures_folder,
            op=self,
            bpy=bpy
        )
        for file in self.files:
            import os.path
            ext = os.path.splitext(file.name)[-1].lower()
            if ext == '.object':
                import_file(self.directory + file.name, cx)
            else:
                self.report({'ERROR'}, 'Format of {} not recognised'.format(file))
        return {'FINISHED'}


class ModelExportHelper:
    selection_only = bpy.props.BoolProperty(
        name='Selection Only',
        description='Export only selected objects'
    )

    def export(self, bpy_obj):
        pass

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, 'No file selected')
            return {'CANCELLED'}
        objs = context.selected_objects if self.selection_only else context.scene.objects
        roots = [o for o in objs if o.xray.isroot]
        if not roots:
            self.report({'ERROR'}, 'Cannot find object root')
            return {'CANCELLED'}
        if len(roots) > 1:
            self.report({'ERROR'}, 'Too many object roots found')
            return {'CANCELLED'}
        return self.export(roots[0])


class OpExportObject(bpy.types.Operator, io_utils.ExportHelper, ModelExportHelper):
    bl_idname = 'xray_export.object'
    bl_label = 'Export .object'

    filename_ext = '.object'
    filter_glob = bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'})

    def export(self, bpy_obj):
        from .fmt_object_exp import export_file
        try:
            export_file(bpy_obj, self.filepath)
        except AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        return {'FINISHED'}


class OpExportOgf(bpy.types.Operator, io_utils.ExportHelper, ModelExportHelper):
    bl_idname = 'xray_export.ogf'
    bl_label = 'Export .ogf'

    filename_ext = '.ogf'
    filter_glob = bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'})

    def export(self, bpy_obj):
        from .fmt_ogf_exp import export_file
        export_file(bpy_obj, self.filepath)
        return {'FINISHED'}


class PluginPreferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    gamedata_folder = bpy.props.StringProperty(name='gamedata', description='The path to the \'gamedata\' directory', subtype='DIR_PATH')
    textures_folder = bpy.props.StringProperty(name='textures', description='The path to the \'gamedata/textures\' directory', subtype='DIR_PATH')

    def get_textures_folder(self):
        result = self.textures_folder;
        if not result and self.gamedata_folder:
            import os.path
            result = os.path.join(self.gamedata_folder, 'textures')
        return result

    def draw(self, context):
        layout = self.layout
        if not self.textures_folder and self.gamedata_folder:
            self.textures_folder = self.get_textures_folder()
        layout.prop(self, 'textures_folder')


def overlay_view_3d():
    def try_draw(base_obj, obj):
        if not hasattr(obj, 'xray'):
            return
        x = obj.xray
        if hasattr(x, 'ondraw_postview'):
            x.ondraw_postview(base_obj, obj)
        if hasattr(obj, 'type'):
            if obj.type == 'ARMATURE':
                for b in obj.data.bones:
                    try_draw(base_obj, b)

    for o in bpy.data.objects:
        try_draw(o, o)


#noinspection PyUnusedLocal
def menu_func_import(self, context):
    self.layout.operator(OpImportObject.bl_idname, text='X-Ray object (.object)')


def menu_func_export(self, context):
    self.layout.operator(OpExportObject.bl_idname, text='X-Ray object (.object)')


def menu_func_export_ogf(self, context):
    self.layout.operator(OpExportOgf.bl_idname, text='X-Ray game object (.ogf)')


def register():
    bpy.utils.register_class(PluginPreferences)
    bpy.utils.register_class(OpImportObject)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.utils.register_class(OpExportObject)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.utils.register_class(OpExportOgf)
    bpy.types.INFO_MT_file_export.append(menu_func_export_ogf)
    overlay_view_3d.__handle = bpy.types.SpaceView3D.draw_handler_add(overlay_view_3d, (), 'WINDOW', 'POST_VIEW')
    inject_init()


def unregister():
    inject_done()
    bpy.types.SpaceView3D.draw_handler_remove(overlay_view_3d.__handle, 'WINDOW')
    bpy.types.INFO_MT_file_export.remove(menu_func_export_ogf)
    bpy.utils.unregister_class(OpExportOgf)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(OpExportObject)
    bpy.utils.unregister_class(OpImportObject)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(PluginPreferences)
