import bpy
from bpy_extras import io_utils
from .xray_inject import inject_init, inject_done


#noinspection PyUnusedLocal
class OpImportObject(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = 'xray_import.object'
    bl_label = 'Import .object'
    bl_description = 'Imports X-Ray object'
    bl_options = {'UNDO'}

    filter_glob = bpy.props.StringProperty(default='*.object', options={'HIDDEN'})

    shaped_bones = bpy.props.BoolProperty(
        name='custom shapes for bones',
        description='use custom shapes for imported bones'
    )

    def execute(self, context):
        addon_prefs = context.user_preferences.addons['io_scene_xray'].preferences
        if not addon_prefs.gamedata_folder:
            self.report({'ERROR'}, 'No gamedata folder specified')
            return {'CANCELLED'}
        filepath_lc = self.properties.filepath.lower()
        if filepath_lc.endswith('.object'):
            from .fmt_object_imp import import_file, ImportContext
            import_file(ImportContext(
                report=self.report,
                gamedata=addon_prefs.gamedata_folder,
                fpath=self.properties.filepath,
                op=self,
                bpy=bpy
            ))
        else:
            if len(filepath_lc) == 0:
                self.report({'ERROR'}, 'No file selected')
            else:
                self.report({'ERROR'}, 'Format of {} not recognised'.format(self.properties.filepath))
            return {'CANCELLED'}
        return {'FINISHED'}


class OpExportObject(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = 'xray_export.object'
    bl_label = 'Export .object'

    filename_ext = '.object'
    filter_glob = bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'})

    selection_only = bpy.props.BoolProperty(
        name='Selection Only',
        description='Export only selected objects'
    )

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
        from .fmt_object_exp import export_file
        export_file(roots[0], self.filepath)
        return {'FINISHED'}


class OpExportOgf(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = 'xray_export.ogf'
    bl_label = 'Export .ogf'

    filename_ext = '.ogf'
    filter_glob = bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'})

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, 'No file selected')
            return {'CANCELLED'}
        if not context.active_object:
            self.report({'ERROR'}, 'No object selected')
            return {'CANCELLED'}
        if context.active_object.type != 'EMPTY':
            self.report({'ERROR'}, 'Unsupported object selected')
            return {'CANCELLED'}
        from .fmt_ogf_exp import export_file
        export_file(context.active_object, self.filepath)
        return {'FINISHED'}


class PluginPreferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    gamedata_folder = bpy.props.StringProperty(name='gamedata', description='The path to the \'gamedata\' directory', subtype='DIR_PATH')

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'gamedata_folder')


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
    inject_init()


def unregister():
    inject_done()
    bpy.types.INFO_MT_file_export.remove(menu_func_export_ogf)
    bpy.utils.unregister_class(OpExportOgf)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(OpExportObject)
    bpy.utils.unregister_class(OpImportObject)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(PluginPreferences)
