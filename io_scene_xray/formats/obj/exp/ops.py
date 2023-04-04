# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from .. import exp
from ... import ie
from ... import contexts
from .... import utils
from .... import log


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

    utils.draw.draw_fmt_ver_prop(layout, self, 'fmt_version')

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
            raise log.AppError('No \'root\'-objects found')
        if len(roots) > 1:
            raise log.AppError(
                'Too many \'root\'-objects found, but none selected'
            )
    return roots


_with_export_motions_props = {
    'export_motions': ie.PropObjectMotionsExport(),
}


class _WithExportMotions:
    if not utils.version.IS_28:
        for prop_name, prop_value in _with_export_motions_props.items():
            exec('{0} = _with_export_motions_props.get("{0}")'.format(prop_name))


filename_ext = '.object'

export_props = {
    'objects': bpy.props.StringProperty(options={'HIDDEN'}),
    'directory': bpy.props.StringProperty(subtype="FILE_PATH"),

    'texture_name_from_image_path': \
        ie.PropObjectTextureNamesFromPath(),

    'fmt_version': ie.PropSDKVersion(),
    'use_export_paths': ie.PropUseExportPaths(),
    'smoothing_out_of': ie.prop_smoothing_out_of()
}


class XRAY_OT_export_object(ie.BaseOperator, _WithExportMotions):
    bl_idname = 'xray_export.object'
    bl_label = 'Export .object'
    bl_options = {'PRESET'}

    text = 'Source Object'
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        utils.ie.open_imp_exp_folder(self, 'objects_folder')
        draw_props(self, mode='BATCH')

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        exp_ctx = ExportObjectContext()

        exp_ctx.texname_from_path = self.texture_name_from_image_path
        exp_ctx.soc_sgroups = self.fmt_version == 'soc'
        exp_ctx.export_motions = self.export_motions
        exp_ctx.smoothing_out_of = self.smoothing_out_of

        for name in self.objects.split(','):
            bpy_obj = context.scene.objects[name]
            name = utils.ie.add_file_ext(name, filename_ext)
            path = self.directory

            if self.use_export_paths and bpy_obj.xray.export_path:
                path = os.path.join(path, bpy_obj.xray.export_path)
                os.makedirs(path, exist_ok=True)

            try:
                exp.export_file(
                    bpy_obj,
                    os.path.join(path, name),
                    exp_ctx
                )
            except log.AppError as err:
                exp_ctx.errors.append(err)

        for err in exp_ctx.errors:
            log.err(err)

        return {'FINISHED'}

    def invoke(self, context, _event):
        try:
            roots = find_objects_for_export(context)
        except log.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        if len(roots) == 1:
            return bpy.ops.xray_export.object_file('INVOKE_DEFAULT')

        self.objects = ','.join([obj.name for obj in roots])

        pref = utils.version.get_preferences()

        self.fmt_version = pref.export_object_sdk_version
        self.export_motions = pref.object_motions_export
        self.texture_name_from_image_path = pref.object_texture_names_from_path
        self.smoothing_out_of = pref.smoothing_out_of
        self.use_export_paths = pref.export_object_use_export_paths

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


export_props = {
    'object': bpy.props.StringProperty(options={'HIDDEN'}),
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'texture_name_from_image_path': \
        ie.PropObjectTextureNamesFromPath(),
    'fmt_version': ie.PropSDKVersion(),
    'smoothing_out_of': ie.prop_smoothing_out_of()
}


class XRAY_OT_export_object_file(
        ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper,
        _WithExportMotions
    ):

    bl_idname = 'xray_export.object_file'
    bl_label = 'Export .object'
    bl_options = {'PRESET'}

    filename_ext = '.object'
    props = export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        utils.ie.open_imp_exp_folder(self, 'objects_folder')
        draw_props(self)

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        export_context = ExportObjectContext()

        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.soc_sgroups = self.fmt_version == 'soc'
        export_context.export_motions = self.export_motions
        export_context.smoothing_out_of = self.smoothing_out_of

        bpy_obj = context.scene.objects[self.object]

        try:
            exp.export_file(bpy_obj, self.filepath, export_context)
        except log.AppError as err:
            export_context.errors.append(err)

        for err in export_context.errors:
            log.err(err)

        return {'FINISHED'}

    def invoke(self, context, event):
        pref = utils.version.get_preferences()

        try:
            roots = find_objects_for_export(context)
        except log.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        if len(roots) > 1:
            self.report({'ERROR'}, 'Too many \'root\'-objects selected')
            return {'CANCELLED'}

        self.object = roots[0].name
        self.filepath = utils.ie.add_file_ext(self.object, filename_ext)

        # set defaults
        self.fmt_version = pref.export_object_sdk_version
        self.export_motions = pref.object_motions_export
        self.texture_name_from_image_path = pref.object_texture_names_from_path
        self.smoothing_out_of = pref.smoothing_out_of

        return super().invoke(context, event)


export_props = {
    'filepath': bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'SKIP_SAVE'}
    ),
    'use_selection': bpy.props.BoolProperty()
}


class XRAY_OT_export_project(ie.BaseOperator):
    bl_idname = 'xray_export.project'
    bl_label = 'Export XRay Project'

    props = export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        data = context.scene.xray
        export_context = ExportObjectContext()
        export_context.texname_from_path = data.object_texture_name_from_image_path
        export_context.soc_sgroups = data.fmt_version == 'soc'
        export_context.smoothing_out_of = data.smoothing_out_of
        export_context.export_motions = data.object_export_motions
        path = bpy.path.abspath(self.filepath if self.filepath else data.export_root)
        os.makedirs(path, exist_ok=True)
        for bpy_obj in XRAY_OT_export_project.find_objects(context, self.use_selection):
            name = utils.ie.add_file_ext(bpy_obj.name, filename_ext)
            opath = path
            if bpy_obj.xray.export_path and data.use_export_paths:
                opath = os.path.join(opath, bpy_obj.xray.export_path)
                os.makedirs(opath, exist_ok=True)
            try:
                exp.export_file(bpy_obj, os.path.join(opath, name), export_context)
            except log.AppError as err:
                export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        return {'FINISHED'}

    @staticmethod
    def find_objects(context, use_selection=False):
        objects = context.selected_objects if use_selection else context.scene.objects
        return [obj for obj in objects if obj.xray.isroot]


classes = (
    XRAY_OT_export_object,
    XRAY_OT_export_object_file,
    XRAY_OT_export_project
)


def register():
    utils.version.assign_props(
        [(_with_export_motions_props, _WithExportMotions), ]
    )
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
