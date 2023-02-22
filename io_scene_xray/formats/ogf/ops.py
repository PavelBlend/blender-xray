# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from .. import ie
from .. import contexts
from ... import log
from ... import utils


class ExportOgfContext(
        contexts.ExportMeshContext,
        contexts.ExportAnimationContext
    ):
    def __init__(self):
        super().__init__()
        self.fmt_ver = None
        self.hq_export = None


op_text = 'Game Object'
filename_ext = '.ogf'


def draw_props(self, context, batch):
    layout = self.layout
    utils.draw.draw_fmt_ver_prop(layout, self, 'fmt_version')
    layout.prop(self, 'export_motions')
    row = layout.row()
    row.active = self.fmt_version == 'cscop' and self.export_motions
    row.prop(self, 'hq_export', text='High Quatily Motions')
    if batch:
        layout.prop(self, 'use_export_paths')
    layout.prop(self, 'texture_name_from_image_path')


export_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'texture_name_from_image_path': ie.PropObjectTextureNamesFromPath(),
    'fmt_version': ie.PropSDKVersion(),
    'hq_export': ie.prop_omf_high_quality(),
    'export_motions': ie.PropObjectMotionsExport()
}


class XRAY_OT_export_ogf_file(
        ie.BaseOperator,
        bpy_extras.io_utils.ExportHelper
    ):
    bl_idname = 'xray_export.ogf_file'
    bl_label = 'Export .ogf'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        draw_props(self, context, False)

    @log.execute_with_logger
    @utils.execute_require_filepath
    @utils.ie.set_initial_state
    def execute(self, context):
        export_context = ExportOgfContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.fmt_ver = self.fmt_version
        export_context.hq_export = self.hq_export
        export_context.export_motions = self.export_motions
        try:
            exp.export_file(self.exported_object, self.filepath, export_context)
        except log.AppError as err:
            export_context.errors.append(err)
        for err in export_context.errors:
            log.err(err)
        for obj in self.selected_objects:
            utils.version.select_object(obj)
        utils.version.set_active_object(self.exported_object)
        return {'FINISHED'}

    def invoke(self, context, event):
        pref = utils.version.get_preferences()

        self.texture_name_from_image_path = pref.ogf_texture_names_from_path
        self.fmt_version = pref.ogf_export_fmt_ver
        self.export_motions = pref.ogf_export_motions
        self.hq_export = pref.ogf_export_hq_motions

        self.filepath = context.active_object.name
        if not self.filepath.lower().endswith(filename_ext):
            self.filepath += filename_ext
        objs = context.selected_objects
        self.selected_objects = context.selected_objects
        roots = [obj for obj in objs if obj.xray.isroot]
        if not roots:
            self.report({'ERROR'}, 'Cannot find object root')
            return {'CANCELLED'}
        if len(roots) > 1:
            self.report({'ERROR'}, 'Too many object roots found')
            return {'CANCELLED'}
        self.exported_object = roots[0]
        return super().invoke(context, event)


batch_export_props = {
    'directory': bpy.props.StringProperty(
        subtype="FILE_PATH",
        options={'HIDDEN'}
    ),
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'texture_name_from_image_path': ie.PropObjectTextureNamesFromPath(),
    'export_motions': ie.PropObjectMotionsExport(),
    'fmt_version': ie.PropSDKVersion(),
    'hq_export': ie.prop_omf_high_quality(),
    'use_export_paths': ie.PropUseExportPaths()
}


class XRAY_OT_export_ogf(ie.BaseOperator):
    bl_idname = 'xray_export.ogf'
    bl_label = 'Export .ogf'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    text = op_text
    ext = filename_ext
    filename_ext = filename_ext
    props = batch_export_props

    if not utils.version.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        draw_props(self, context, True)

    @log.execute_with_logger
    @utils.ie.set_initial_state
    def execute(self, context):
        export_context = ExportOgfContext()
        export_context.texname_from_path = self.texture_name_from_image_path
        export_context.export_motions = self.export_motions
        export_context.fmt_ver = self.fmt_version
        export_context.hq_export = self.hq_export

        for obj in self.roots:
            file_name = obj.name
            if not file_name.endswith(filename_ext):
                file_name += filename_ext

            path = self.directory
            exp_path = obj.xray.export_path
            if self.use_export_paths and exp_path:
                path = os.path.join(path, exp_path)
                os.makedirs(path, exist_ok=True)
            file_path = os.path.join(path, file_name)

            try:
                exp.export_file(obj, file_path, export_context)
            except log.AppError as err:
                export_context.errors.append(err)

        for err in export_context.errors:
            log.err(err)

        return {'FINISHED'}

    def invoke(self, context, event):
        pref = utils.version.get_preferences()

        self.use_export_paths = pref.ogf_export_use_export_paths
        self.export_motions = pref.ogf_export_motions
        self.texture_name_from_image_path = pref.ogf_texture_names_from_path
        self.fmt_version = pref.ogf_export_fmt_ver
        self.hq_export = pref.ogf_export_hq_motions

        self.roots = [
            obj
            for obj in context.selected_objects
                if obj.xray.isroot
        ]

        if not self.roots:
            self.report({'ERROR'}, 'Cannot find root-objects')
            return {'CANCELLED'}

        if len(self.roots) == 1:
            return bpy.ops.xray_export.ogf_file('INVOKE_DEFAULT')

        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


classes = (
    imp.ops.XRAY_OT_import_ogf,
    XRAY_OT_export_ogf,
    XRAY_OT_export_ogf_file
)


def register():
    utils.version.register_operators(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
