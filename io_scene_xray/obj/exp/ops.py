import os

import bpy
import bpy_extras

from ... import registry
from ... import ops
from ... import plugin_prefs
from ... import utils
from .. import exp


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
            raise utils.AppError('No \'root\'-objects found')
        if len(roots) > 1:
            raise utils.AppError(
                'Too many \'root\'-objects found, but none selected'
            )
    return roots


class _WithExportMotions:
    export_motions = plugin_prefs.PropObjectMotionsExport()


@registry.module_thing
class OpExportObjects(ops.BaseOperator, _WithExportMotions):
    bl_idname = 'export_object.xray_objects'
    bl_label = 'Export selected .object-s'

    objects = bpy.props.StringProperty(options={'HIDDEN'})

    directory = bpy.props.StringProperty(subtype="FILE_PATH")

    texture_name_from_image_path = \
        plugin_prefs.PropObjectTextureNamesFromPath()

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

    @utils.execute_with_logger
    def execute(self, context):
        export_context = utils.mk_export_context(
            self.texture_name_from_image_path,
            self.fmt_version, self.export_motions
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
                exp.export_file(
                    obj, os.path.join(path, name), export_context
                )
        except utils.AppError as err:
            raise err
        return {'FINISHED'}

    def invoke(self, context, _event):
        prefs = plugin_prefs.get_preferences()
        roots = None
        try:
            roots = find_objects_for_export(context)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}
        if len(roots) == 1:
            return bpy.ops.xray_export.object('INVOKE_DEFAULT')
        self.objects = ','.join([o.name for o in roots])
        self.fmt_version = prefs.sdk_version
        self.export_motions = prefs.object_motions_export
        self.texture_name_from_image_path = \
            prefs.object_texture_names_from_path
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


@registry.module_thing
class OpExportObject(
        ops.BaseOperator,
        bpy_extras.io_utils.ExportHelper,
        _WithExportMotions
    ):

    bl_idname = 'xray_export.object'
    bl_label = 'Export .object'

    object = bpy.props.StringProperty(options={'HIDDEN'})

    filename_ext = '.object'
    filter_glob = bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    )

    texture_name_from_image_path = \
        plugin_prefs.PropObjectTextureNamesFromPath()

    fmt_version = plugin_prefs.PropSDKVersion()

    def draw(self, _context):
        layout = self.layout

        row = layout.split()
        row.label('Format Version:')
        row.row().prop(self, 'fmt_version', expand=True)

        layout.prop(self, 'export_motions')
        layout.prop(self, 'texture_name_from_image_path')

    @utils.execute_with_logger
    def execute(self, context):
        export_context = utils.mk_export_context(
            self.texture_name_from_image_path,
            self.fmt_version,
            self.export_motions
        )
        try:
            exp.export_file(
                context.scene.objects[self.object],
                self.filepath, export_context
            )
        except utils.AppError as err:
            raise err
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
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
        if not self.filepath.lower().endswith(self.filename_ext):
            self.filepath += self.filename_ext
        self.fmt_version = prefs.sdk_version
        self.export_motions = prefs.object_motions_export
        self.texture_name_from_image_path = \
            prefs.object_texture_names_from_path
        return super().invoke(context, event)
