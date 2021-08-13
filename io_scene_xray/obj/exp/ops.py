# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from .. import exp
from ... import ops
from ... import icons
from ... import utils
from ... import contexts
from ... import obj
from ... import version_utils
from ... import plugin_props


class ExportObjectContext(
        contexts.ExportMeshContext,
        contexts.ExportAnimationContext
    ):

    def __init__(self):
        contexts.ExportMeshContext.__init__(self)
        contexts.ExportAnimationContext.__init__(self)
        self.soc_sgroups = None
        self.smoothing_out_of = None


def find_objects_for_export(context):
    processed = set()
    roots = []
    for bpy_obj in context.selected_objects:
        while bpy_obj:
            if bpy_obj in processed:
                break
            processed.add(bpy_obj)
            if bpy_obj.xray.isroot:
                roots.append(bpy_obj)
                break
            bpy_obj = bpy_obj.parent
    if not roots:
        roots = [
            bpy_obj
            for bpy_obj in context.scene.objects
                if bpy_obj.xray.isroot
        ]
        if not roots:
            raise utils.AppError('No \'root\'-objects found')
        if len(roots) > 1:
            raise utils.AppError(
                'Too many \'root\'-objects found, but none selected'
            )
    return roots


_with_export_motions_props = {
    'export_motions': plugin_props.PropObjectMotionsExport(),
}


class _WithExportMotions:
    if not version_utils.IS_28:
        for prop_name, prop_value in _with_export_motions_props.items():
            exec('{0} = _with_export_motions_props.get("{0}")'.format(prop_name))


op_export_object_props = {
    'objects': bpy.props.StringProperty(options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype="FILE_PATH"),

    'texture_name_from_image_path': \
        plugin_props.PropObjectTextureNamesFromPath(),

    'fmt_version': plugin_props.PropSDKVersion(),
    'use_export_paths': plugin_props.PropUseExportPaths(),
    'smoothing_out_of': plugin_props.prop_smoothing_out_of()
}


class XRAY_OT_export_object(ops.base.BaseOperator, _WithExportMotions):
    bl_idname = 'xray_export.object'
    bl_label = 'Export .object'
    bl_options = {'PRESET'}

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_object_props.items():
            exec('{0} = op_export_object_props.get("{0}")'.format(prop_name))

    def draw(self, _context):
        layout = self.layout

        row = layout.split()
        row.label(text='Format Version:')
        row.row().prop(self, 'fmt_version', expand=True)
        row = layout.row()
        row.label(text='Smoothing Out of:')
        row.prop(self, 'smoothing_out_of', text='')

        layout.prop(self, 'use_export_paths')
        layout.prop(self, 'export_motions')
        layout.prop(self, 'texture_name_from_image_path')

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        export_context = ExportObjectContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.soc_sgroups = self.fmt_version == 'soc'
        export_context.export_motions = self.export_motions
        export_context.smoothing_out_of = self.smoothing_out_of
        preferences = version_utils.get_preferences()
        export_context.textures_folder = preferences.textures_folder_auto
        try:
            for name in self.objects.split(','):
                bpy_obj = context.scene.objects[name]
                if not name.lower().endswith('.object'):
                    name += '.object'
                path = self.directory
                if self.use_export_paths and bpy_obj.xray.export_path:
                    path = os.path.join(path, bpy_obj.xray.export_path)
                    os.makedirs(path, exist_ok=True)
                exp.export_file(
                    bpy_obj, os.path.join(path, name), export_context
                )
            if self.smoothing_out_of == 'SPLIT_NORMALS':
                for name in self.objects.split(','):
                    bpy_obj = context.scene.objects[name]
                    version_utils.select_object(bpy_obj)
        except utils.AppError as err:
            raise err
        return {'FINISHED'}

    def invoke(self, context, _event):
        preferences = version_utils.get_preferences()
        roots = None
        try:
            roots = find_objects_for_export(context)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        if len(roots) == 1:
            return bpy.ops.xray_export.object_file('INVOKE_DEFAULT')
        self.objects = ','.join([o.name for o in roots])
        self.fmt_version = preferences.export_object_sdk_version
        self.export_motions = preferences.object_motions_export
        self.texture_name_from_image_path = \
            preferences.object_texture_names_from_path
        self.smoothing_out_of = preferences.smoothing_out_of
        self.use_export_paths = preferences.export_object_use_export_paths
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


filename_ext = '.object'
op_export_single_object_props = {
    'object': bpy.props.StringProperty(options={'HIDDEN'}),
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'texture_name_from_image_path': \
        plugin_props.PropObjectTextureNamesFromPath(),
    'fmt_version': plugin_props.PropSDKVersion(),
    'smoothing_out_of': plugin_props.prop_smoothing_out_of()
}


class XRAY_OT_export_single_object(
        ops.base.BaseOperator,
        bpy_extras.io_utils.ExportHelper,
        _WithExportMotions
    ):

    bl_idname = 'xray_export.object_file'
    bl_label = 'Export .object'
    bl_options = {'PRESET'}

    filename_ext = '.object'

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_single_object_props.items():
            exec('{0} = op_export_single_object_props.get("{0}")'.format(prop_name))

    def draw(self, _context):
        layout = self.layout

        row = layout.split()
        row.label(text='Format Version:')
        row.row().prop(self, 'fmt_version', expand=True)
        row = layout.row()
        row.label(text='Smoothing Out of:')
        row.prop(self, 'smoothing_out_of', text='')

        layout.prop(self, 'export_motions')
        layout.prop(self, 'texture_name_from_image_path')

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        export_context = ExportObjectContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.soc_sgroups = self.fmt_version == 'soc'
        export_context.export_motions = self.export_motions
        export_context.smoothing_out_of = self.smoothing_out_of
        bpy_obj = context.scene.objects[self.object]
        preferences = version_utils.get_preferences()
        export_context.textures_folder = preferences.textures_folder_auto
        try:
            exp.export_file(bpy_obj, self.filepath, export_context)
        except utils.AppError as err:
            raise err
        if self.smoothing_out_of == 'SPLIT_NORMALS':
            version_utils.set_active_object(bpy_obj)
            version_utils.select_object(bpy_obj)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        roots = None
        try:
            roots = find_objects_for_export(context)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        if len(roots) > 1:
            self.report({'ERROR'}, 'Too many \'root\'-objects selected')
            return {'CANCELLED'}
        self.object = roots[0].name
        self.filepath = self.object
        if not self.filepath.lower().endswith(filename_ext):
            self.filepath += filename_ext
        self.fmt_version = preferences.export_object_sdk_version
        self.export_motions = preferences.object_motions_export
        self.texture_name_from_image_path = \
            preferences.object_texture_names_from_path
        self.smoothing_out_of = preferences.smoothing_out_of
        return super().invoke(context, event)


def menu_func_export(self, _context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_object.bl_idname,
        text='X-Ray object (.object)',
        icon_value=icon
    )


op_export_project_props = {
    'filepath': bpy.props.StringProperty(subtype='DIR_PATH', options={'SKIP_SAVE'}),
    'use_selection': bpy.props.BoolProperty()
}


class XRAY_OT_export_project(ops.base.BaseOperator):
    bl_idname = 'xray_export.project'
    bl_label = 'Export XRay Project'

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_project_props.items():
            exec('{0} = op_export_project_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    def execute(self, context):
        data = context.scene.xray
        export_context = obj.exp.ops.ExportObjectContext()
        export_context.texname_from_path = data.object_texture_name_from_image_path
        export_context.soc_sgroups = data.fmt_version == 'soc'
        export_context.export_motions = data.object_export_motions
        try:
            path = bpy.path.abspath(self.filepath if self.filepath else data.export_root)
            os.makedirs(path, exist_ok=True)
            for bpy_obj in XRAY_OT_export_project.find_objects(context, self.use_selection):
                name = bpy_obj.name
                if not name.lower().endswith('.object'):
                    name += '.object'
                opath = path
                if bpy_obj.xray.export_path:
                    opath = os.path.join(opath, bpy_obj.xray.export_path)
                    os.makedirs(opath, exist_ok=True)
                obj.exp.export_file(bpy_obj, os.path.join(opath, name), export_context)
        except utils.AppError as err:
            raise err
        return {'FINISHED'}

    @staticmethod
    def find_objects(context, use_selection=False):
        objects = context.selected_objects if use_selection else context.scene.objects
        return [o for o in objects if o.xray.isroot]


classes = (
    (XRAY_OT_export_object, op_export_object_props),
    (XRAY_OT_export_single_object, op_export_single_object_props),
    (XRAY_OT_export_project, op_export_project_props)
)


def register():
    version_utils.assign_props(
        [(_with_export_motions_props, _WithExportMotions), ]
    )
    for operator, props in classes:
        version_utils.assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
