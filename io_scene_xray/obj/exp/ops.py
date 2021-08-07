import os

import bpy
import bpy_extras

from ... import ops, ui, utils, context, prefs
from ...version_utils import (
    assign_props, IS_28, set_active_object, select_object
)
from .. import exp, props as general_obj_props
from ...ops.base import BaseOperator as TestReadyOperator
from . import props


class ExportObjectContext(
        context.ExportMeshContext,
        context.ExportAnimationContext
    ):

    def __init__(self):
        context.ExportMeshContext.__init__(self)
        context.ExportAnimationContext.__init__(self)
        self.soc_sgroups = None
        self.smoothing_out_of = None


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


_with_export_motions_props = {
    'export_motions': props.PropObjectMotionsExport(),
}


class _WithExportMotions:
    if not IS_28:
        for prop_name, prop_value in _with_export_motions_props.items():
            exec('{0} = _with_export_motions_props.get("{0}")'.format(prop_name))


op_export_object_props = {
    'objects': bpy.props.StringProperty(options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype="FILE_PATH"),

    'texture_name_from_image_path': \
        props.PropObjectTextureNamesFromPath(),

    'fmt_version': general_obj_props.PropSDKVersion(),
    'use_export_paths': props.PropUseExportPaths(),
    'smoothing_out_of': props.prop_smoothing_out_of()
}


class XRAY_OT_export_object(ops.base.BaseOperator, _WithExportMotions):
    bl_idname = 'xray_export.object'
    bl_label = 'Export selected .object-s'
    bl_options = {'PRESET'}

    if not IS_28:
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
        preferences = prefs.utils.get_preferences()
        export_context.textures_folder = preferences.textures_folder_auto
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
            if self.smoothing_out_of == 'SPLIT_NORMALS':
                for name in self.objects.split(','):
                    obj = context.scene.objects[name]
                    select_object(obj)
        except utils.AppError as err:
            raise err
        return {'FINISHED'}

    def invoke(self, context, _event):
        preferences = prefs.utils.get_preferences()
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
        props.PropObjectTextureNamesFromPath(),
    'fmt_version': general_obj_props.PropSDKVersion(),
    'smoothing_out_of': props.prop_smoothing_out_of()
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

    if not IS_28:
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
        obj = context.scene.objects[self.object]
        preferences = prefs.utils.get_preferences()
        export_context.textures_folder = preferences.textures_folder_auto
        try:
            exp.export_file(obj, self.filepath, export_context)
        except utils.AppError as err:
            raise err
        if self.smoothing_out_of == 'SPLIT_NORMALS':
            set_active_object(obj)
            select_object(obj)
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = prefs.utils.get_preferences()
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
    icon = ui.icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_object.bl_idname,
        text='X-Ray object (.object)',
        icon_value=icon
    )


op_export_project_props = {
    'filepath': bpy.props.StringProperty(subtype='DIR_PATH', options={'SKIP_SAVE'}),
    'use_selection': bpy.props.BoolProperty()
}


class XRAY_OT_export_project(TestReadyOperator):
    bl_idname = 'xray_export.project'
    bl_label = 'Export XRay Project'

    if not IS_28:
        for prop_name, prop_value in op_export_project_props.items():
            exec('{0} = op_export_project_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    def execute(self, context):
        from ..exp import export_file, ops as object_exp_ops
        from bpy.path import abspath
        data = context.scene.xray

        export_context = object_exp_ops.ExportObjectContext()
        export_context.texname_from_path = data.object_texture_name_from_image_path
        export_context.soc_sgroups = data.fmt_version == 'soc'
        export_context.export_motions = data.object_export_motions
        try:
            path = abspath(self.filepath if self.filepath else data.export_root)
            os.makedirs(path, exist_ok=True)
            for obj in XRAY_OT_export_project.find_objects(context, self.use_selection):
                name = obj.name
                if not name.lower().endswith('.object'):
                    name += '.object'
                opath = path
                if obj.xray.export_path:
                    opath = os.path.join(opath, obj.xray.export_path)
                    os.makedirs(opath, exist_ok=True)
                export_file(obj, os.path.join(opath, name), export_context)
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
    assign_props([(_with_export_motions_props, _WithExportMotions), ])
    for operator, props in classes:
        assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
