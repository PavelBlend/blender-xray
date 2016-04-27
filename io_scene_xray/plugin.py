import bpy
from bpy_extras import io_utils
from .xray_inject import inject_init, inject_done
from .utils import AppError
from .plugin_prefs import PluginPreferences, get_preferences


def _create_prop_soc_smoothing_groups():
    return bpy.props.BoolProperty(
        default=True,
        name='SoC smoothing groups',
        description='use SoC smoothing group format'
    )


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

    soc_smoothing_groups = _create_prop_soc_smoothing_groups()

    def execute(self, context):
        textures_folder = get_preferences().get_textures_folder()
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
            soc_sgroups=self.soc_smoothing_groups,
            op=self,
            bpy=bpy
        )
        for file in self.files:
            import os.path
            ext = os.path.splitext(file.name)[-1].lower()
            if ext == '.object':
                cx.before_import_file();
                import_file(self.directory + file.name, cx)
            else:
                self.report({'ERROR'}, 'Format of {} not recognised'.format(file))
        return {'FINISHED'}


class OpImportAnm(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = 'xray_import.anm'
    bl_label = 'Import .anm'
    bl_description = 'Imports X-Ray animation'
    bl_options = {'UNDO'}

    filter_glob = bpy.props.StringProperty(default='*.anm', options={'HIDDEN'})

    directory = bpy.props.StringProperty(subtype='DIR_PATH')
    files = bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)

    camera_animation = bpy.props.BoolProperty(
        name='Create Linked Camera',
        description='Create animated camera object (linked to "empty"-object)'
    )

    def execute(self, context):
        if len(self.files) == 0:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        from .fmt_anm_imp import import_file, ImportContext
        cx = ImportContext(
            report=self.report,
            camera_animation=self.camera_animation
        )
        for file in self.files:
            import os.path
            ext = os.path.splitext(file.name)[-1].lower()
            if ext == '.anm':
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
        return self.export(roots[0], context)


def find_objects_for_export(context):
    processed = set()
    roots = []
    for o in context.selected_objects:
        while o:
            if o in processed:
                break
            processed.add(o)
            if o.xray.isroot:
                roots.append(o)
                break
            o = o.parent
    if len(roots) == 0:
        roots = [o for o in context.scene.objects if o.xray.isroot]
        if len(roots) == 0:
            raise AppError('No \'root\'-objects found')
        if len(roots) > 1:
            raise AppError('Too many \'root\'-objects found, but none selected')
    return roots


def _texture_name_from_image_path():
    return bpy.props.BoolProperty(
        name='texture names from image paths',
        description='generate texture names from image paths (by subtract <gamedata/textures> prefix & <file-extension> suffix)'
    )


def _mk_export_context(context, report, texname_from_path, soc_smoothing_groups = None):
        from .fmt_object_exp import ExportContext
        return ExportContext(
            textures_folder=get_preferences().get_textures_folder(),
            report=report,
            soc_sgroups=soc_smoothing_groups,
            texname_from_path=texname_from_path
        )


class OpExportObjects(bpy.types.Operator):
    bl_idname = 'export_object.xray_objects'
    bl_label = 'Export selected .object-s'

    objects = bpy.props.StringProperty(options={'HIDDEN'})

    directory = bpy.props.StringProperty(subtype="FILE_PATH")

    texture_name_from_image_path = _texture_name_from_image_path()

    soc_smoothing_groups = _create_prop_soc_smoothing_groups()

    def execute(self, context):
        from .fmt_object_exp import export_file
        cx = _mk_export_context(context, self.report, self.texture_name_from_image_path, self.soc_smoothing_groups)
        import os.path
        try:
            for n in self.objects.split(','):
                o = context.scene.objects[n]
                if not n.lower().endswith('.object'):
                    n += '.object'
                export_file(o, os.path.join(self.directory, n), cx)
        except AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        roots = None
        try:
            roots = find_objects_for_export(context)
        except AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        if len(roots) == 1:
            return bpy.ops.xray_export.object('INVOKE_DEFAULT')
        self.objects = ','.join([o.name for o in roots])
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class OpExportObject(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = 'xray_export.object'
    bl_label = 'Export .object'

    object = bpy.props.StringProperty(options={'HIDDEN'})

    filename_ext = '.object'
    filter_glob = bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'})

    texture_name_from_image_path = _texture_name_from_image_path()

    soc_smoothing_groups = _create_prop_soc_smoothing_groups()

    def execute(self, context):
        from .fmt_object_exp import export_file
        cx = _mk_export_context(context, self.report, self.texture_name_from_image_path, self.soc_smoothing_groups)
        try:
            export_file(context.scene.objects[self.object], self.filepath, cx)
        except AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        roots = None
        try:
            roots = find_objects_for_export(context)
        except AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        if len(roots) > 1:
            self.report({'ERROR'}, 'Too many \'root\'-objects selected')
            return {'CANCELLED'}
        self.object = roots[0].name
        self.filepath = self.object
        if not self.filepath.lower().endswith(self.filename_ext):
            self.filepath += self.filename_ext
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class OpExportOgf(bpy.types.Operator, io_utils.ExportHelper, ModelExportHelper):
    bl_idname = 'xray_export.ogf'
    bl_label = 'Export .ogf'

    filename_ext = '.ogf'
    filter_glob = bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'})

    texture_name_from_image_path = _texture_name_from_image_path()

    def export(self, bpy_obj, context):
        from .fmt_ogf_exp import export_file
        cx = _mk_export_context(context, self.report, self.texture_name_from_image_path)
        export_file(bpy_obj, self.filepath, cx)
        return {'FINISHED'}


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
    self.layout.operator(OpImportAnm.bl_idname, text='X-Ray animation (.anm)')


def menu_func_export(self, context):
    self.layout.operator(OpExportObjects.bl_idname, text='X-Ray object (.object)')


def menu_func_export_ogf(self, context):
    self.layout.operator(OpExportOgf.bl_idname, text='X-Ray game object (.ogf)')


def register():
    bpy.utils.register_class(PluginPreferences)
    bpy.utils.register_class(OpImportObject)
    bpy.utils.register_class(OpImportAnm)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.utils.register_class(OpExportObject)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.utils.register_class(OpExportObjects)
    bpy.utils.register_class(OpExportOgf)
    bpy.types.INFO_MT_file_export.append(menu_func_export_ogf)
    overlay_view_3d.__handle = bpy.types.SpaceView3D.draw_handler_add(overlay_view_3d, (), 'WINDOW', 'POST_VIEW')
    inject_init()


def unregister():
    inject_done()
    bpy.types.SpaceView3D.draw_handler_remove(overlay_view_3d.__handle, 'WINDOW')
    bpy.types.INFO_MT_file_export.remove(menu_func_export_ogf)
    bpy.utils.unregister_class(OpExportOgf)
    bpy.utils.unregister_class(OpExportObjects)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(OpExportObject)
    bpy.utils.unregister_class(OpImportAnm)
    bpy.utils.unregister_class(OpImportObject)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(PluginPreferences)
