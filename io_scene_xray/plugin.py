import os.path
import re

import bpy
import bpy.utils.previews
from bpy_extras import io_utils

from . import xray_inject, xray_io
from .ops import (
    BaseOperator as TestReadyOperator, convert_materials, shader_tools
)
from .ui import collapsible, motion_list
from .utils import (
    AppError, ObjectsInitializer, logger, execute_with_logger,
    execute_require_filepath, FilenameExtHelper, mk_export_context
)
from . import plugin_prefs
from . import registry
from .details import ops as det_ops
from .dm import ops as dm_ops
from .err import ops as err_ops
from .scene import ops as scene_ops
from .obj.exp import ops as object_exp_ops
from .obj.imp import ops as object_imp_ops
from .anm import ops as anm_ops
from .skl import ops as skl_ops
from .ogf import ops as ogf_ops
from .level import ops as level_ops
from .omf import ops as omf_ops
from . import skls_browser
from .version_utils import (
    get_import_export_menus, get_scene_update_post, assign_props, IS_28
)


xray_io.ENCODE_ERROR = AppError

op_export_project_props = {
    'filepath': bpy.props.StringProperty(subtype='DIR_PATH', options={'SKIP_SAVE'}),
    'use_selection': bpy.props.BoolProperty()
}

@registry.module_thing
class OpExportProject(TestReadyOperator):
    bl_idname = 'export_scene.xray'
    bl_label = 'Export XRay Project'

    if not IS_28:
        for prop_name, prop_value in op_export_project_props.items():
            exec('{0} = op_export_project_props.get("{0}")'.format(prop_name))

    @execute_with_logger
    def execute(self, context):
        from .obj.exp import export_file
        from bpy.path import abspath
        data = context.scene.xray
        export_context = mk_export_context(
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


assign_props([
    (op_export_project_props, OpExportProject),
])


@registry.module_thing
class XRayImportMenu(bpy.types.Menu):
    bl_idname = 'INFO_MT_xray_import'
    bl_label = 'X-Ray'

    def draw(self, context):
        layout = self.layout

        layout.operator(
            object_imp_ops.OpImportObject.bl_idname,
            text='Source Object (.object)'
        )
        layout.operator(anm_ops.OpImportAnm.bl_idname, text='Animation (.anm)')
        layout.operator(skl_ops.OpImportSkl.bl_idname, text='Skeletal Animation (.skl, .skls)')
        layout.operator(det_ops.OpImportDetails.bl_idname, text='Level Details (.details)')
        layout.operator(dm_ops.OpImportDM.bl_idname, text='Detail Model (.dm)')
        layout.operator(err_ops.OpImportERR.bl_idname, text='Error List (.err)')
        layout.operator(scene_ops.OpImportLevelScene.bl_idname, text='Scene Selection (.level)')
        layout.operator(omf_ops.IMPORT_OT_xray_omf.bl_idname, text='Game Motion (.omf)')
        if IS_28:
            layout.operator(level_ops.IMPORT_OT_xray_level.bl_idname, text='Game Level (level)')


@registry.module_thing
class XRayExportMenu(bpy.types.Menu):
    bl_idname = 'INFO_MT_xray_export'
    bl_label = 'X-Ray'

    def draw(self, context):
        layout = self.layout

        layout.operator(
            object_exp_ops.OpExportObjects.bl_idname,
            text='Source Object (.object)'
        )
        layout.operator(anm_ops.OpExportAnm.bl_idname, text='Animation (.anm)')
        layout.operator(skl_ops.OpExportSkls.bl_idname, text='Skeletal Animation (.skls)')
        layout.operator(ogf_ops.OpExportOgf.bl_idname, text='Game Object (.ogf)')
        layout.operator(dm_ops.OpExportDMs.bl_idname, text='Detail Model (.dm)')
        layout.operator(
            det_ops.OpExportDetails.bl_idname,
            text='Level Details (.details)'
        )
        layout.operator(scene_ops.OpExportLevelScene.bl_idname, text='Scene Selection (.level)')
        layout.operator(omf_ops.EXPORT_OT_xray_omf.bl_idname, text='Game Motion (.omf)')
        if IS_28:
            layout.operator(level_ops.EXPORT_OT_xray_level.bl_idname, text='Game Level (level)')


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
    icon = get_stalker_icon()
    self.layout.operator(
        object_imp_ops.OpImportObject.bl_idname,
        text='X-Ray object (.object)',
        icon_value=icon
    )
    self.layout.operator(anm_ops.OpImportAnm.bl_idname, text='X-Ray animation (.anm)', icon_value=icon)
    self.layout.operator(skl_ops.OpImportSkl.bl_idname, text='X-Ray skeletal animation (.skl, .skls)', icon_value=icon)


def menu_func_export(self, _context):
    icon = get_stalker_icon()
    self.layout.operator(
        object_exp_ops.OpExportObjects.bl_idname,
        text='X-Ray object (.object)',
        icon_value=icon
    )
    self.layout.operator(anm_ops.OpExportAnm.bl_idname, text='X-Ray animation (.anm)', icon_value=icon)
    self.layout.operator(skl_ops.OpExportSkls.bl_idname, text='X-Ray animation (.skls)', icon_value=icon)


def menu_func_export_ogf(self, _context):
    icon = get_stalker_icon()
    self.layout.operator(ogf_ops.OpExportOgf.bl_idname, text='X-Ray game object (.ogf)', icon_value=icon)


def menu_func_xray_import(self, _context):
    icon = get_stalker_icon()
    self.layout.menu(XRayImportMenu.bl_idname, icon_value=icon)


def menu_func_xray_export(self, _context):
    icon = get_stalker_icon()
    self.layout.menu(XRayExportMenu.bl_idname, icon_value=icon)


def append_menu_func():
    prefs = plugin_prefs.get_preferences()
    import_menu, export_menu = get_import_export_menus()
    if prefs.compact_menus:
        import_menu.remove(menu_func_import)
        export_menu.remove(menu_func_export)
        export_menu.remove(menu_func_export_ogf)
        import_menu.remove(err_ops.menu_func_import)
        import_menu.remove(det_ops.menu_func_import)
        export_menu.remove(det_ops.menu_func_export)
        import_menu.remove(dm_ops.menu_func_import)
        export_menu.remove(dm_ops.menu_func_export)
        export_menu.remove(scene_ops.menu_func_export)
        import_menu.remove(scene_ops.menu_func_import)
        import_menu.remove(omf_ops.menu_func_import)
        import_menu.remove(omf_ops.menu_func_export)
        if IS_28:
            import_menu.remove(level_ops.menu_func_import)
            export_menu.remove(level_ops.menu_func_export)
        import_menu.prepend(menu_func_xray_import)
        export_menu.prepend(menu_func_xray_export)
    else:
        import_menu.remove(menu_func_xray_import)
        export_menu.remove(menu_func_xray_export)
        import_menu.append(menu_func_import)
        export_menu.append(menu_func_export)
        export_menu.append(menu_func_export_ogf)
        import_menu.append(det_ops.menu_func_import)
        export_menu.append(det_ops.menu_func_export)
        import_menu.append(dm_ops.menu_func_import)
        export_menu.append(dm_ops.menu_func_export)
        import_menu.append(err_ops.menu_func_import)
        export_menu.append(scene_ops.menu_func_export)
        import_menu.append(scene_ops.menu_func_import)
        import_menu.append(omf_ops.menu_func_import)
        import_menu.append(omf_ops.menu_func_export)
        if IS_28:
            import_menu.append(level_ops.menu_func_import)
            export_menu.append(level_ops.menu_func_export)


registry.module_requires(__name__, [
    plugin_prefs,
    xray_inject,
])


preview_collections = {}
STALKER_ICON_NAME = 'stalker'


def get_stalker_icon():
    pcoll = preview_collections['main']
    icon = pcoll[STALKER_ICON_NAME]
    # without this line in some cases the icon is not visible
    len(icon.icon_pixels)
    return icon.icon_id


def register():
    # load icon
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    pcoll.load(STALKER_ICON_NAME, os.path.join(icons_dir, 'stalker.png'), 'IMAGE')
    preview_collections['main'] = pcoll

    registry.register_thing(object_imp_ops, __name__)
    registry.register_thing(object_exp_ops, __name__)
    registry.register_thing(anm_ops, __name__)
    registry.register_thing(skl_ops, __name__)
    registry.register_thing(ogf_ops, __name__)
    registry.register_thing(motion_list, __name__)
    registry.register_thing(omf_ops, __name__)
    scene_ops.register_operators()
    if IS_28:
        level_ops.register_operators()
    convert_materials.register()
    shader_tools.register()
    det_ops.register_operators()
    dm_ops.register_operators()
    registry.register_thing(err_ops, __name__)
    append_menu_func()
    overlay_view_3d.__handle = bpy.types.SpaceView3D.draw_handler_add(
        overlay_view_3d, (),
        'WINDOW', 'POST_VIEW'
    )
    bpy.app.handlers.load_post.append(load_post)
    get_scene_update_post().append(scene_update_post)
    registry.register_thing(skls_browser, __name__)


def unregister():
    registry.unregister_thing(skls_browser, __name__)
    registry.unregister_thing(err_ops, __name__)
    dm_ops.unregister_operators()
    det_ops.unregister_operators()
    if IS_28:
        level_ops.unregister_operators()
    shader_tools.unregister()
    convert_materials.unregister()
    scene_ops.unregister_operators()
    registry.unregister_thing(omf_ops, __name__)
    registry.unregister_thing(motion_list, __name__)
    registry.unregister_thing(ogf_ops, __name__)
    registry.unregister_thing(skl_ops, __name__)
    registry.unregister_thing(anm_ops, __name__)
    registry.unregister_thing(object_exp_ops, __name__)
    registry.unregister_thing(object_imp_ops, __name__)

    get_scene_update_post().remove(scene_update_post)
    bpy.app.handlers.load_post.remove(load_post)
    bpy.types.SpaceView3D.draw_handler_remove(overlay_view_3d.__handle, 'WINDOW')
    import_menu, export_menu = get_import_export_menus()
    export_menu.remove(menu_func_export_ogf)
    export_menu.remove(menu_func_export)
    import_menu.remove(menu_func_import)
    import_menu.remove(menu_func_xray_import)
    export_menu.remove(menu_func_xray_export)

    # remove icon
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
