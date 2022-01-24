# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from .. import exp
from ... import icons
from ... import utils
from ... import log
from ... import contexts
from ... import obj
from ... import version_utils
from ... import ie_props


class ExportObjectContext(
        contexts.ExportMeshContext,
        contexts.ExportAnimationContext
    ):

    def __init__(self):
        super().__init__()
        self.soc_sgroups = None
        self.smoothing_out_of = None


def draw_props(self, mode='SINGLE'):
    layout = self.layout

    utils.draw_fmt_ver_prop(layout, self, 'fmt_version')

    row = layout.split()
    row.label(text='Smoothing:')
    row.row().prop(self, 'smoothing_out_of', expand=True)

    if mode == 'BATCH':
        layout.prop(self, 'use_export_paths')
    layout.prop(self, 'export_motions')
    layout.prop(self, 'texture_name_from_image_path')


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
    'export_motions': ie_props.PropObjectMotionsExport(),
}


class _WithExportMotions:
    if not version_utils.IS_28:
        for prop_name, prop_value in _with_export_motions_props.items():
            exec('{0} = _with_export_motions_props.get("{0}")'.format(prop_name))


filename_ext = '.object'

op_export_object_props = {
    'objects': bpy.props.StringProperty(options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype="FILE_PATH"),

    'texture_name_from_image_path': \
        ie_props.PropObjectTextureNamesFromPath(),

    'fmt_version': ie_props.PropSDKVersion(),
    'use_export_paths': ie_props.PropUseExportPaths(),
    'smoothing_out_of': ie_props.prop_smoothing_out_of()
}


class XRAY_OT_export_object(ie_props.BaseOperator, _WithExportMotions):
    bl_idname = 'xray_export.object'
    bl_label = 'Export .object'
    bl_options = {'PRESET'}

    text = 'Source Object'
    ext = filename_ext
    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_object_props.items():
            exec('{0} = op_export_object_props.get("{0}")'.format(prop_name))

    def draw(self, context):
        draw_props(self, mode='BATCH')

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
        use_split_normals = self.smoothing_out_of == 'SPLIT_NORMALS'
        active_object, selected_objects = utils.get_selection_state(context)
        for name in self.objects.split(','):
            bpy_obj = context.scene.objects[name]
            if not name.lower().endswith('.object'):
                name += '.object'
            path = self.directory
            if self.use_export_paths and bpy_obj.xray.export_path:
                path = os.path.join(path, bpy_obj.xray.export_path)
                os.makedirs(path, exist_ok=True)
            try:
                exp.export_file(
                    bpy_obj,
                    os.path.join(path, name),
                    export_context
                )
            except utils.AppError as err:
                export_context.errors.append(err)
        utils.set_selection_state(active_object, selected_objects)
        for err in export_context.errors:
            log.err(err)
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
        self.objects = ','.join([obj.name for obj in roots])
        self.fmt_version = preferences.export_object_sdk_version
        self.export_motions = preferences.object_motions_export
        self.texture_name_from_image_path = \
            preferences.object_texture_names_from_path
        self.smoothing_out_of = preferences.smoothing_out_of
        self.use_export_paths = preferences.export_object_use_export_paths
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


op_export_single_object_props = {
    'object': bpy.props.StringProperty(options={'HIDDEN'}),
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'texture_name_from_image_path': \
        ie_props.PropObjectTextureNamesFromPath(),
    'fmt_version': ie_props.PropSDKVersion(),
    'smoothing_out_of': ie_props.prop_smoothing_out_of()
}


class XRAY_OT_export_object_file(
        ie_props.BaseOperator,
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

    def draw(self, context):
        draw_props(self)

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
        use_split_normals = self.smoothing_out_of == 'SPLIT_NORMALS'
        active_object, selected_objects = utils.get_selection_state(context)
        try:
            exp.export_file(bpy_obj, self.filepath, export_context)
        except utils.AppError as err:
            export_context.errors.append(err)
        utils.set_selection_state(active_object, selected_objects)
        for err in export_context.errors:
            log.err(err)
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


op_export_project_props = {
    'filepath': bpy.props.StringProperty(subtype='DIR_PATH', options={'SKIP_SAVE'}),
    'use_selection': bpy.props.BoolProperty()
}


class XRAY_OT_export_project(ie_props.BaseOperator):
    bl_idname = 'xray_export.project'
    bl_label = 'Export XRay Project'

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_project_props.items():
            exec('{0} = op_export_project_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        data = context.scene.xray
        export_context = ExportObjectContext()
        export_context.texname_from_path = data.object_texture_name_from_image_path
        export_context.soc_sgroups = data.fmt_version == 'soc'
        export_context.export_motions = data.object_export_motions
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
            try:
                exp.export_file(bpy_obj, os.path.join(opath, name), export_context)
            except utils.AppError as err:
                export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        return {'FINISHED'}

    @staticmethod
    def find_objects(context, use_selection=False):
        objects = context.selected_objects if use_selection else context.scene.objects
        return [obj for obj in objects if obj.xray.isroot]


classes = (
    (XRAY_OT_export_object, op_export_object_props),
    (XRAY_OT_export_object_file, op_export_single_object_props),
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
