import bpy
from .xray_inject import inject_init, inject_done


#noinspection PyUnusedLocal
class OpImportObject(bpy.types.Operator):
    bl_idname = 'xray_import.object'
    bl_label = 'Import .object'
    bl_description = 'Imports source STALKER model data'
    bl_options = {'UNDO'}

    # Properties used by the file browser
    filepath = bpy.props.StringProperty(
        name='File path', description='File filepath used for importing the .object file',
        maxlen=1024, default=''
    )
    filter_folder = bpy.props.BoolProperty(name='Filter folders', description='', default=True, options={'HIDDEN'})
    filter_glob = bpy.props.StringProperty(default='*.object', options={'HIDDEN'})

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
                bpy=bpy
            ))
        else:
            if len(filepath_lc) == 0:
                self.report({'ERROR'}, 'No file selected')
            else:
                self.report({'ERROR'}, 'Format of {} not recognised'.format(self.properties.filepath))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class PluginPreferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    gamedata_folder = bpy.props.StringProperty(name='gamedata', description='The path to the \'gamedata\' directory', subtype='DIR_PATH')

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'gamedata_folder')


#noinspection PyUnusedLocal
def menu_func_import(self, context):
    self.layout.operator(OpImportObject.bl_idname, text='STALKER (.object)')


def register():
    bpy.utils.register_class(PluginPreferences)
    bpy.utils.register_class(OpImportObject)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    inject_init()


def unregister():
    inject_done()
    bpy.utils.unregister_class(OpImportObject)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(PluginPreferences)
