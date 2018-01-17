import os.path

import bpy
from bpy_extras import io_utils

from . import xray_inject
from .ops import BaseOperator as TestReadyOperator
from .utils import AppError, ObjectsInitializer, logger
from . import plugin_prefs
from . import registry


def execute_with_logger(method):
    def wrapper(self, context):
        with logger(self.__class__.bl_idname, self.report):
            return method(self, context)

    return wrapper


#noinspection PyUnusedLocal
@registry.module_thing
class OpImportObject(TestReadyOperator, io_utils.ImportHelper):
    bl_idname = 'xray_import.object'
    bl_label = 'Import .object'
    bl_description = 'Imports X-Ray object'
    bl_options = {'UNDO'}

    filter_glob = bpy.props.StringProperty(default='*.object', options={'HIDDEN'})

    directory = bpy.props.StringProperty(subtype="DIR_PATH")
    files = bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)

    import_motions = plugin_prefs.PropObjectMotionsImport()
    mesh_split_by_materials = plugin_prefs.PropObjectMeshSplitByMaterials()

    shaped_bones = plugin_prefs.PropObjectBonesCustomShapes()

    fmt_version = plugin_prefs.PropSDKVersion()

    @execute_with_logger
    def execute(self, _context):
        textures_folder = plugin_prefs.get_preferences().get_textures_folder()
        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')
        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        from .fmt_object_imp import import_file, ImportContext
        import_context = ImportContext(
            textures=textures_folder,
            soc_sgroups=self.fmt_version == 'soc',
            import_motions=self.import_motions,
            split_by_materials=self.mesh_split_by_materials,
            operator=self,
        )
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            if ext == '.object':
                import_context.before_import_file()
                import_file(os.path.join(self.directory, file.name), import_context)
            else:
                self.report({'ERROR'}, 'Format of {} not recognised'.format(file))
        return {'FINISHED'}

    def draw(self, _context):
        layout = self.layout
        row = layout.row()
        row.enabled = False
        row.label('%d items' % len(self.files))

        row = layout.split()
        row.label('Format Version:')
        row.row().prop(self, 'fmt_version', expand=True)

        layout.prop(self, 'import_motions')
        layout.prop(self, 'mesh_split_by_materials')
        layout.prop(self, 'shaped_bones')

    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
        self.fmt_version = prefs.sdk_version
        self.import_motions = prefs.object_motions_import
        self.mesh_split_by_materials = prefs.object_mesh_split_by_mat
        self.shaped_bones = prefs.object_bones_custom_shapes
        return super().invoke(context, event)


@registry.module_thing
class OpImportAnm(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = 'xray_import.anm'
    bl_label = 'Import .anm'
    bl_description = 'Imports X-Ray animation'
    bl_options = {'UNDO'}

    filter_glob = bpy.props.StringProperty(default='*.anm', options={'HIDDEN'})

    directory = bpy.props.StringProperty(subtype='DIR_PATH')
    files = bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)

    camera_animation = plugin_prefs.PropAnmCameraAnimation()

    @execute_with_logger
    def execute(self, _context):
        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        from .fmt_anm_imp import import_file, ImportContext
        import_context = ImportContext(
            camera_animation=self.camera_animation
        )
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            if ext == '.anm':
                import_file(os.path.join(self.directory, file.name), import_context)
            else:
                self.report({'ERROR'}, 'Format of {} not recognised'.format(file))
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
        self.camera_animation = prefs.anm_create_camera
        return super().invoke(context, event)


def invoke_require_armature(func):
    def wrapper(self, context, event):
        active = context.active_object
        if (not active) or (active.type != 'ARMATURE'):
            self.report({'ERROR'}, 'Active is not armature')
            return {'CANCELLED'}
        return func(self, context, event)

    return wrapper


@registry.module_thing
@registry.requires('Motion')
class OpImportSkl(TestReadyOperator, io_utils.ImportHelper):
    class Motion(bpy.types.PropertyGroup):
        name = bpy.props.StringProperty()

    bl_idname = 'xray_import.skl'
    bl_label = 'Import .skl/.skls'
    bl_description = 'Imports X-Ray skeletal amination'
    bl_options = {'UNDO'}

    filter_glob = bpy.props.StringProperty(default='*.skl;*.skls', options={'HIDDEN'})

    directory = bpy.props.StringProperty(subtype='DIR_PATH')
    files = bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)

    motions_preview_items = bpy.props.CollectionProperty(type=Motion)
    motions_preview_index = bpy.props.IntProperty()
    __parsed_file_name = None

    def draw(self, _context):
        layout = self.layout
        row = layout.row()
        row.enabled = False
        row.label('%d items' % len(self.files))

        if len(self._get_motions()) > 1:
            layout.template_list(
                'UI_UL_list', 'name',
                self, 'motions_preview_items',
                self, 'motions_preview_index',
            )

    def _get_motions(self):
        if len(self.files) == 1:
            fpath = os.path.join(self.directory, self.files[0].name)
            if self.__parsed_file_name != fpath:
                items = self.motions_preview_items
                items.clear()
                for name in self._examine_file(fpath):
                    items.add().name = name
            self.__parsed_file_name = fpath
        else:
            self.motions_preview_items.clear()

        return self.motions_preview_items

    @staticmethod
    def _examine_file(fpath):
        if fpath.lower().endswith('.skls'):
            from .xray_io import PackedReader
            from .xray_motions import examine_motions
            with open(fpath, 'rb') as file:
                reader = PackedReader(file.read())
                return examine_motions(reader)
        return tuple()

    @execute_with_logger
    def execute(self, context):
        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        from .fmt_skl_imp import import_skl_file, import_skls_file, ImportContext
        import_context = ImportContext(
            armature=context.active_object
        )
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            fpath = os.path.join(self.directory, file.name)
            if ext == '.skl':
                import_skl_file(fpath, import_context)
            elif ext == '.skls':
                import_skls_file(fpath, import_context)
            else:
                self.report({'ERROR'}, 'Format of {} not recognised'.format(file))
        return {'FINISHED'}

    @invoke_require_armature
    def invoke(self, context, event):
        return super().invoke(context, event)


def execute_require_filepath(func):
    def wrapper(self, context):
        if not self.filepath:
            self.report({'ERROR'}, 'No file selected')
            return {'CANCELLED'}
        return func(self, context)

    return wrapper


@registry.module_thing
class OpImportDM(TestReadyOperator, io_utils.ImportHelper):
    bl_idname = 'xray_import.dm'
    bl_label = 'Import .dm/.details'
    bl_description = 'Imports X-Ray Detail Model (.dm, .details)'
    bl_options = {'UNDO'}

    filter_glob = bpy.props.StringProperty(default='*.dm;*.details', options={'HIDDEN'})

    directory = bpy.props.StringProperty(subtype="DIR_PATH")
    files = bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)

    @execute_with_logger
    def execute(self, _context):
        textures_folder = plugin_prefs.get_preferences().get_textures_folder()
        if not textures_folder:
            self.report({'WARNING'}, 'No textures folder specified')
        if not self.files:
            self.report({'ERROR'}, 'No files selected')
            return {'CANCELLED'}
        from . import fmt_dm_imp
        from . import fmt_details_imp
        from .fmt_object_imp import ImportContext
        import_context = ImportContext(
            textures=textures_folder,
            soc_sgroups=None,
            import_motions=None,
            split_by_materials=None,
            operator=self,
        )
        try:
            for file in self.files:
                ext = os.path.splitext(file.name)[-1].lower()
                fpath = os.path.join(self.directory, file.name)
                if ext == '.dm':
                    fmt_dm_imp.import_file(fpath, import_context)
                elif ext == '.details':
                    fmt_details_imp.import_file(fpath, import_context)
                else:
                    self.report({'ERROR'}, 'Format of {} not recognised'.format(file))
        finally:
            pass
        return {'FINISHED'}

    def draw(self, _context):
        layout = self.layout
        row = layout.row()
        row.enabled = False
        row.label('%d items' % len(self.files))


class ModelExportHelper:
    selection_only = bpy.props.BoolProperty(
        name='Selection Only',
        description='Export only selected objects'
    )

    def export(self, bpy_obj, context):
        pass

    @execute_with_logger
    @execute_require_filepath
    def execute(self, context):
        objs = context.selected_objects if self.selection_only else context.scene.objects
        roots = [obj for obj in objs if obj.xray.isroot]
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
    for obj in context.selected_objects:
        while obj:
            if obj in processed:
                break
            processed.add(obj)
            if obj.xray.isroot:
                roots.append(obj)
                break
            obj = obj.parent
    if not roots:
        roots = [obj for obj in context.scene.objects if obj.xray.isroot]
        if not roots:
            raise AppError('No \'root\'-objects found')
        if len(roots) > 1:
            raise AppError('Too many \'root\'-objects found, but none selected')
    return roots


def _mk_export_context(texname_from_path, fmt_version=None, export_motions=True):
    from .fmt_object_exp import ExportContext
    return ExportContext(
        textures_folder=plugin_prefs.get_preferences().get_textures_folder(),
        export_motions=export_motions,
        soc_sgroups=None if fmt_version is None else (fmt_version == 'soc'),
        texname_from_path=texname_from_path
    )


class _WithExportMotions:
    export_motions = plugin_prefs.PropObjectMotionsExport()


@registry.module_thing
class OpExportObjects(TestReadyOperator, _WithExportMotions):
    bl_idname = 'export_object.xray_objects'
    bl_label = 'Export selected .object-s'

    objects = bpy.props.StringProperty(options={'HIDDEN'})

    directory = bpy.props.StringProperty(subtype="FILE_PATH")

    texture_name_from_image_path = plugin_prefs.PropObjectTextureNamesFromPath()

    fmt_version = plugin_prefs.PropSDKVersion()

    use_export_paths = plugin_prefs.PropUseExportPaths()

    def draw(self, _context):
        layout = self.layout

        row = layout.split()
        row.label('Format Version:')
        row.row().prop(self, 'fmt_version', expand=True)

        layout.prop(self, 'use_export_paths')
        layout.prop(self, 'export_motions')
        layout.prop(self, 'texture_name_from_image_path')

    @execute_with_logger
    def execute(self, context):
        from .fmt_object_exp import export_file
        export_context = _mk_export_context(
            self.texture_name_from_image_path, self.fmt_version, self.export_motions
        )
        try:
            for name in self.objects.split(','):
                obj = context.scene.objects[name]
                if not name.lower().endswith('.object'):
                    name += '.object'
                path = self.directory
                if self.use_export_paths and obj.xray.export_path:
                    path = os.path.join(path, obj.xray.export_path)
                    os.makedirs(path, exist_ok=True)
                export_file(obj, os.path.join(path, name), export_context)
        except AppError as err:
            raise err
        return {'FINISHED'}

    def invoke(self, context, _event):
        prefs = plugin_prefs.get_preferences()
        roots = None
        try:
            roots = find_objects_for_export(context)
        except AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        if len(roots) == 1:
            return bpy.ops.xray_export.object('INVOKE_DEFAULT')
        self.objects = ','.join([o.name for o in roots])
        self.fmt_version = prefs.sdk_version
        self.export_motions = prefs.object_motions_export
        self.texture_name_from_image_path = prefs.object_texture_names_from_path
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


@registry.module_thing
class OpExportObject(bpy.types.Operator, io_utils.ExportHelper, _WithExportMotions):
    bl_idname = 'xray_export.object'
    bl_label = 'Export .object'

    object = bpy.props.StringProperty(options={'HIDDEN'})

    filename_ext = '.object'
    filter_glob = bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'})

    texture_name_from_image_path = plugin_prefs.PropObjectTextureNamesFromPath()

    fmt_version = plugin_prefs.PropSDKVersion()

    def draw(self, _context):
        layout = self.layout

        row = layout.split()
        row.label('Format Version:')
        row.row().prop(self, 'fmt_version', expand=True)

        layout.prop(self, 'export_motions')
        layout.prop(self, 'texture_name_from_image_path')

    @execute_with_logger
    def execute(self, context):
        from .fmt_object_exp import export_file
        export_context = _mk_export_context(
            self.texture_name_from_image_path, self.fmt_version, self.export_motions
        )
        try:
            export_file(context.scene.objects[self.object], self.filepath, export_context)
        except AppError as err:
            raise err
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
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
        self.fmt_version = prefs.sdk_version
        self.export_motions = prefs.object_motions_export
        self.texture_name_from_image_path = prefs.object_texture_names_from_path
        return super().invoke(context, event)


@registry.module_thing
class OpExportDM(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = 'xray_export.dm'
    bl_label = 'Export .dm'

    filename_ext = '.dm'
    filter_glob = bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'})

    texture_name_from_image_path = plugin_prefs.PropObjectTextureNamesFromPath()

    @execute_with_logger
    def execute(self, context):
        objs = context.selected_objects
        if not objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}
        if len(objs) > 1:
            self.report({'ERROR'}, 'Too many selected objects found')
            return {'CANCELLED'}
        if objs[0].type != 'MESH':
            self.report({'ERROR'}, 'The selected object is not a mesh')
            return {'CANCELLED'}
        try:
            self.export(objs[0], context)
        except AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        return {'FINISHED'}

    def export(self, bpy_obj, context):
        from .fmt_dm_exp import export_file
        export_context = _mk_export_context(self.texture_name_from_image_path)
        export_file(bpy_obj, self.filepath, export_context)


    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
        self.texture_name_from_image_path = prefs.object_texture_names_from_path
        return super().invoke(context, event)


@registry.module_thing
class OpExportOgf(bpy.types.Operator, io_utils.ExportHelper, ModelExportHelper):
    bl_idname = 'xray_export.ogf'
    bl_label = 'Export .ogf'

    filename_ext = '.ogf'
    filter_glob = bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'})

    texture_name_from_image_path = plugin_prefs.PropObjectTextureNamesFromPath()

    def export(self, bpy_obj, context):
        from .fmt_ogf_exp import export_file
        export_context = _mk_export_context(self.texture_name_from_image_path)
        export_file(bpy_obj, self.filepath, export_context)
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
        self.texture_name_from_image_path = prefs.object_texture_names_from_path
        return super().invoke(context, event)


class FilenameExtHelper(io_utils.ExportHelper):
    def export(self, context):
        pass

    @execute_with_logger
    @execute_require_filepath
    def execute(self, context):
        self.export(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = context.active_object.name
        if not self.filepath.lower().endswith(self.filename_ext):
            self.filepath += self.filename_ext
        return super().invoke(context, event)


@registry.module_thing
class OpExportAnm(bpy.types.Operator, FilenameExtHelper):
    bl_idname = 'xray_export.anm'
    bl_label = 'Export .anm'
    bl_description = 'Exports X-Ray animation'

    filename_ext = '.anm'
    filter_glob = bpy.props.StringProperty(default='*'+filename_ext, options={'HIDDEN'})

    def export(self, context):
        from .fmt_anm_exp import export_file
        export_file(context.active_object, self.filepath)


@registry.module_thing
class OpExportSkl(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = 'xray_export.skl'
    bl_label = 'Export .skl'
    bl_description = 'Exports X-Ray skeletal animation'

    filename_ext = '.skl'
    filter_glob = bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'})
    action = None

    @execute_with_logger
    @execute_require_filepath
    def execute(self, context):
        from .fmt_skl_exp import export_skl_file, ExportContext
        export_context = ExportContext(
            armature=context.active_object,
            action=self.action
        )
        export_skl_file(self.filepath, export_context)
        return {'FINISHED'}

    @invoke_require_armature
    def invoke(self, context, event):
        self.action = getattr(context, OpExportSkl.bl_idname + '.action', None)
        assert self.action
        self.filepath = self.action.name
        if not self.filepath.lower().endswith(self.filename_ext):
            self.filepath += self.filename_ext
        return super().invoke(context, event)


@registry.module_thing
class OpExportSkls(bpy.types.Operator, FilenameExtHelper):
    bl_idname = 'xray_export.skls'
    bl_label = 'Export .skls'
    bl_description = 'Exports X-Ray skeletal animation'

    filename_ext = '.skls'
    filter_glob = bpy.props.StringProperty(default='*' + filename_ext, options={'HIDDEN'})

    def export(self, context):
        from .fmt_skl_exp import export_skls_file, ExportContext
        export_context = ExportContext(
            armature=context.active_object
        )
        export_skls_file(self.filepath, export_context)

    @invoke_require_armature
    def invoke(self, context, event):
        return super().invoke(context, event)


@registry.module_thing
class OpExportProject(TestReadyOperator):
    bl_idname = 'export_scene.xray'
    bl_label = 'Export XRay Project'

    filepath = bpy.props.StringProperty(subtype='DIR_PATH', options={'SKIP_SAVE'})
    use_selection = bpy.props.BoolProperty()

    @execute_with_logger
    def execute(self, context):
        from .fmt_object_exp import export_file
        from bpy.path import abspath
        data = context.scene.xray
        export_context = _mk_export_context(
            data.object_texture_name_from_image_path, data.fmt_version, data.object_export_motions
        )
        try:
            path = abspath(self.filepath if self.filepath else data.export_root)
            os.makedirs(path, exist_ok=True)
            for obj in OpExportProject.find_objects(context, self.use_selection):
                name = obj.name
                if not name.lower().endswith('.object'):
                    name += '.object'
                opath = path
                if obj.xray.export_path:
                    opath = os.path.join(opath, obj.xray.export_path)
                    os.makedirs(opath, exist_ok=True)
                export_file(obj, os.path.join(opath, name), export_context)
        except AppError as err:
            raise err
        return {'FINISHED'}

    @staticmethod
    def find_objects(context, use_selection=False):
        objects = context.selected_objects if use_selection else context.scene.objects
        return [o for o in objects if o.xray.isroot]


def overlay_view_3d():
    def try_draw(base_obj, obj):
        if not hasattr(obj, 'xray'):
            return
        xray = obj.xray
        if hasattr(xray, 'ondraw_postview'):
            xray.ondraw_postview(base_obj, obj)
        if hasattr(obj, 'type'):
            if obj.type == 'ARMATURE':
                for bone in obj.data.bones:
                    try_draw(base_obj, bone)

    for obj in bpy.data.objects:
        try_draw(obj, obj)


_INITIALIZER = ObjectsInitializer([
    'objects',
    'materials',
])

@bpy.app.handlers.persistent
def load_post(_):
    _INITIALIZER.sync('LOADED', bpy.data)

@bpy.app.handlers.persistent
def scene_update_post(_):
    _INITIALIZER.sync('CREATED', bpy.data)


#noinspection PyUnusedLocal
def menu_func_import(self, _context):
    self.layout.operator(OpImportObject.bl_idname, text='X-Ray object (.object)')
    self.layout.operator(OpImportAnm.bl_idname, text='X-Ray animation (.anm)')
    self.layout.operator(OpImportSkl.bl_idname, text='X-Ray skeletal animation (.skl, .skls)')
    self.layout.operator(OpImportDM.bl_idname, text='X-Ray detail model (.dm, .details)')


def menu_func_export(self, _context):
    self.layout.operator(OpExportObjects.bl_idname, text='X-Ray object (.object)')
    self.layout.operator(OpExportAnm.bl_idname, text='X-Ray animation (.anm)')
    self.layout.operator(OpExportSkls.bl_idname, text='X-Ray animation (.skls)')
    self.layout.operator(OpExportDM.bl_idname, text='X-Ray detail model (.dm)')


def menu_func_export_ogf(self, _context):
    self.layout.operator(OpExportOgf.bl_idname, text='X-Ray game object (.ogf)')


registry.module_requires(__name__, [
    plugin_prefs,
    xray_inject,
])

def register():
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.types.INFO_MT_file_export.append(menu_func_export_ogf)
    overlay_view_3d.__handle = bpy.types.SpaceView3D.draw_handler_add(
        overlay_view_3d, (),
        'WINDOW', 'POST_VIEW'
    )
    bpy.app.handlers.load_post.append(load_post)
    bpy.app.handlers.scene_update_post.append(scene_update_post)


def unregister():
    bpy.app.handlers.scene_update_post.remove(scene_update_post)
    bpy.app.handlers.load_post.remove(load_post)
    bpy.types.SpaceView3D.draw_handler_remove(overlay_view_3d.__handle, 'WINDOW')
    bpy.types.INFO_MT_file_export.remove(menu_func_export_ogf)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
