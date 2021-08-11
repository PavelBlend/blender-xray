# standart modules
import os
import re

# blender modules
import bpy
import bpy.utils.previews
from bpy_extras import io_utils

# addon modules
from . import xray_io
from . import ops
from . import ui
from . import plugin_prefs
from . import edit_helpers
from . import hotkeys
from . import props
from . import skls_browser
from . import icons
from .ui import base
from .utils import (
    AppError, ObjectsInitializer, logger,
    execute_require_filepath
)
from .version_utils import (
    get_import_export_menus,
    get_scene_update_post,
    assign_props,
    get_preferences
)

# plugin modules
from . import details
from .details import ops as det_ops
from .dm import ops as dm_ops
from .err import ops as err_ops
from .scene import ops as scene_ops
from .obj.exp import ops as object_exp_ops
from .obj.imp import ops as object_imp_ops
from .anm import ops as anm_ops
from .skl import ops as skl_ops
from .bones import ops as bones_ops
from .ogf import ops as ogf_ops
from .level import ops as level_ops
from .omf import ops as omf_ops


xray_io.ENCODE_ERROR = AppError


class XRayImportMenu(bpy.types.Menu):
    bl_idname = 'INFO_MT_xray_import'
    bl_label = base.build_label()

    def draw(self, context):
        layout = self.layout
        enabled_import_operators = get_enabled_operators(import_draw_functions)
        for id_name, text in enabled_import_operators:
            layout.operator(id_name, text=text)


def get_enabled_operators(draw_functions):
    preferences = get_preferences()
    operators = []
    for _, enable_prop, id_name, text in draw_functions:
        enable = getattr(preferences, enable_prop)
        if enable:
            operators.append((id_name, text))
    return operators


class XRayExportMenu(bpy.types.Menu):
    bl_idname = 'INFO_MT_xray_export'
    bl_label = base.build_label()

    def draw(self, context):
        layout = self.layout
        enabled_export_operators = get_enabled_operators(export_draw_functions)
        for id_name, text in enabled_export_operators:
            layout.operator(id_name, text=text)


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


def menu_func_xray_import(self, _context):
    icon = icons.get_stalker_icon()
    self.layout.menu(XRayImportMenu.bl_idname, icon_value=icon)


def menu_func_xray_export(self, _context):
    icon = icons.get_stalker_icon()
    self.layout.menu(XRayExportMenu.bl_idname, icon_value=icon)


# import draw functions
import_draw_functions = [
    (
        object_imp_ops.menu_func_import,
        'enable_object_import',
        object_imp_ops.XRAY_OT_import_object.bl_idname,
        'Source Object (.object)'
    ),
    (
        anm_ops.menu_func_import,
        'enable_anm_import',
        anm_ops.XRAY_OT_import_anm.bl_idname,
        'Animation (.anm)'
    ),
    (
        skl_ops.menu_func_import,
        'enable_skls_import',
        skl_ops.XRAY_OT_import_skls.bl_idname,
        'Skeletal Animation (.skls)'
    ),
    (
        bones_ops.menu_func_import,
        'enable_bones_import',
        bones_ops.XRAY_OT_import_bones.bl_idname,
        'Bones Data (.bones)'
    ),
    (
        err_ops.menu_func_import,
        'enable_err_import',
        err_ops.XRAY_OT_import_err.bl_idname,
        'Error List (.err)'
    ),
    (
        det_ops.menu_func_import,
        'enable_details_import',
        det_ops.XRAY_OT_import_details.bl_idname,
        'Level Details (.details)'
    ),
    (
        dm_ops.menu_func_import,
        'enable_dm_import',
        dm_ops.XRAY_OT_import_dm.bl_idname,
        'Detail Model (.dm)'
    ),
    (
        scene_ops.menu_func_import,
        'enable_level_import',
        scene_ops.XRAY_OT_import_scene_selection.bl_idname,
        'Scene Selection (.level)'
    ),
    (
        omf_ops.menu_func_import,
        'enable_omf_import',
        omf_ops.XRAY_OT_import_omf.bl_idname,
        'Game Motion (.omf)'
    ),
    (
        level_ops.menu_func_import,
        'enable_game_level_import',
        level_ops.XRAY_OT_import_level.bl_idname,
        'Game Level (level)'
    )
]

# export draw functions
export_draw_functions = [
    (
        object_exp_ops.menu_func_export,
        'enable_object_export',
        object_exp_ops.XRAY_OT_export_object.bl_idname,
        'Source Object (.object)'
    ),
    (
        anm_ops.menu_func_export,
        'enable_anm_export',
        anm_ops.XRAY_OT_export_anm.bl_idname,
        'Animation (.anm)'
    ),
    (
        skl_ops.menu_func_export,
        'enable_skls_export',
        skl_ops.XRAY_OT_export_skls.bl_idname,
        'Skeletal Animation (.skls)'
    ),
    (
        bones_ops.menu_func_export,
        'enable_bones_export',
        bones_ops.XRAY_OT_export_bones.bl_idname,
        'Bones Data (.bones)'
    ),
    (
        ogf_ops.menu_func_export,
        'enable_ogf_export',
        ogf_ops.XRAY_OT_export_ogf.bl_idname,
        'Game Object (.ogf)'
    ),
    (
        det_ops.menu_func_export,
        'enable_details_export',
        det_ops.XRAY_OT_export_details.bl_idname,
        'Level Details (.details)'
    ),
    (
        dm_ops.menu_func_export,
        'enable_dm_export',
        dm_ops.XRAY_OT_export_dm.bl_idname,
        'Detail Model (.dm)'
    ),
    (
        scene_ops.menu_func_export,
        'enable_level_export',
        scene_ops.XRAY_OT_export_scene_selection.bl_idname,
        'Scene Selection (.level)'
    ),
    (
        omf_ops.menu_func_export,
        'enable_omf_export',
        omf_ops.XRAY_OT_export_omf.bl_idname,
        'Game Motion (.omf)'
    ),
    (
        level_ops.menu_func_export,
        'enable_game_level_export',
        level_ops.XRAY_OT_export_level.bl_idname,
        'Game Level (level)'
    )
]


def remove_draw_functions(funct_list, menu):
    for draw_function, _, _, _ in funct_list:
        menu.remove(draw_function)


def append_draw_functions(funct_list, menu):
    preferences = get_preferences()
    for draw_function, enable_prop, _, _ in funct_list:
        enable = getattr(preferences, enable_prop)
        if enable:
            menu.append(draw_function)


def append_menu_func():
    preferences = get_preferences()
    import_menu, export_menu = get_import_export_menus()

    # remove import menus
    remove_draw_functions(import_draw_functions, import_menu)
    # remove export menus
    remove_draw_functions(export_draw_functions, export_menu)
    # remove compact menus
    import_menu.remove(menu_func_xray_import)
    export_menu.remove(menu_func_xray_export)

    if preferences.compact_menus:
        # create compact import menus
        enabled_import_operators = get_enabled_operators(import_draw_functions)
        if enabled_import_operators:
            import_menu.prepend(menu_func_xray_import)
        # create compact export menus
        enabled_export_operators = get_enabled_operators(export_draw_functions)
        if enabled_export_operators:
            export_menu.prepend(menu_func_xray_export)
    else:
        # create standart import menus
        append_draw_functions(import_draw_functions, import_menu)
        # create standart export menus
        append_draw_functions(export_draw_functions, export_menu)


classes = (
    XRayImportMenu,
    XRayExportMenu
)


def register():
    icons.register()
    details.register()
    skls_browser.register()
    props.register()

    for clas in classes:
        bpy.utils.register_class(clas)
    plugin_prefs.register()

    object_imp_ops.register()
    object_exp_ops.register()
    anm_ops.register()
    dm_ops.register()
    bones_ops.register()
    ogf_ops.register()
    skl_ops.register()
    omf_ops.register()
    scene_ops.register()
    level_ops.register()
    err_ops.register()
    append_menu_func()
    overlay_view_3d.__handle = bpy.types.SpaceView3D.draw_handler_add(
        overlay_view_3d, (),
        'WINDOW', 'POST_VIEW'
    )
    bpy.app.handlers.load_post.append(load_post)
    get_scene_update_post().append(scene_update_post)
    hotkeys.register()
    edit_helpers.register()
    ops.register()
    ui.register()


def unregister():
    ui.unregister()
    ops.unregister()
    edit_helpers.unregister()
    hotkeys.unregister()
    err_ops.unregister()
    dm_ops.unregister()
    bones_ops.unregister()
    ogf_ops.unregister()
    level_ops.unregister()
    scene_ops.unregister()
    omf_ops.unregister()
    skl_ops.unregister()
    anm_ops.unregister()
    object_exp_ops.unregister()
    object_imp_ops.unregister()

    get_scene_update_post().remove(scene_update_post)
    bpy.app.handlers.load_post.remove(load_post)
    bpy.types.SpaceView3D.draw_handler_remove(overlay_view_3d.__handle, 'WINDOW')

    import_menu, export_menu = get_import_export_menus()

    # remove import menus
    remove_draw_functions(import_draw_functions, import_menu)
    # remove export menus
    remove_draw_functions(export_draw_functions, export_menu)
    # remove compact menus
    import_menu.remove(menu_func_xray_import)
    export_menu.remove(menu_func_xray_export)

    plugin_prefs.unregister()
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)

    props.unregister()
    skls_browser.unregister()
    details.unregister()
    icons.unregister()
