# blender modules
import bpy

# addon modules
from . import ops
from . import ui
from . import plugin_prefs
from . import edit_helpers
from . import hotkeys
from . import props
from . import skls_browser
from . import icons
from . import utils
from . import version_utils
from . import xray_io

# plugin modules
from . import details
from . import dm
from . import err
from . import scene
from . import obj
from . import anm
from . import skl
from . import bones
from . import ogf
from . import level
from . import omf


xray_io.ENCODE_ERROR = utils.AppError


def get_enabled_operators(draw_functions):
    preferences = version_utils.get_preferences()
    operators = []
    for _, enable_prop, id_name, text in draw_functions:
        enable = getattr(preferences, enable_prop)
        if enable:
            operators.append((id_name, text))
    return operators


class XRAY_MT_import(bpy.types.Menu):
    bl_idname = 'XRAY_MT_import'
    bl_label = ui.base.build_label()

    def draw(self, context):
        layout = self.layout
        import_operators = get_enabled_operators(import_draw_functions)
        for id_name, text in import_operators:
            layout.operator(id_name, text=text)


class XRAY_MT_export(bpy.types.Menu):
    bl_idname = 'XRAY_MT_export'
    bl_label = ui.base.build_label()

    def draw(self, context):
        layout = self.layout
        export_operators = get_enabled_operators(export_draw_functions)
        for id_name, text in export_operators:
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


_INITIALIZER = utils.ObjectsInitializer([
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
    self.layout.menu(XRAY_MT_import.bl_idname, icon_value=icon)


def menu_func_xray_export(self, _context):
    icon = icons.get_stalker_icon()
    self.layout.menu(XRAY_MT_export.bl_idname, icon_value=icon)


# import draw functions
import_draw_functions = [
    (
        obj.imp.ops.menu_func_import,
        'enable_object_import',
        obj.imp.ops.XRAY_OT_import_object.bl_idname,
        'Source Object (.object)'
    ),
    (
        anm.ops.menu_func_import,
        'enable_anm_import',
        anm.ops.XRAY_OT_import_anm.bl_idname,
        'Animation (.anm)'
    ),
    (
        skl.ops.menu_func_import,
        'enable_skls_import',
        skl.ops.XRAY_OT_import_skls.bl_idname,
        'Skeletal Animation (.skls)'
    ),
    (
        bones.ops.menu_func_import,
        'enable_bones_import',
        bones.ops.XRAY_OT_import_bones.bl_idname,
        'Bones Data (.bones)'
    ),
    (
        err.ops.menu_func_import,
        'enable_err_import',
        err.ops.XRAY_OT_import_err.bl_idname,
        'Error List (.err)'
    ),
    (
        details.ops.menu_func_import,
        'enable_details_import',
        details.ops.XRAY_OT_import_details.bl_idname,
        'Level Details (.details)'
    ),
    (
        dm.ops.menu_func_import,
        'enable_dm_import',
        dm.ops.XRAY_OT_import_dm.bl_idname,
        'Detail Model (.dm)'
    ),
    (
        scene.ops.menu_func_import,
        'enable_level_import',
        scene.ops.XRAY_OT_import_scene_selection.bl_idname,
        'Scene Selection (.level)'
    ),
    (
        omf.ops.menu_func_import,
        'enable_omf_import',
        omf.ops.XRAY_OT_import_omf.bl_idname,
        'Game Motion (.omf)'
    ),
    (
        level.ops.menu_func_import,
        'enable_game_level_import',
        level.ops.XRAY_OT_import_level.bl_idname,
        'Game Level (level)'
    )
]

# export draw functions
export_draw_functions = [
    (
        obj.exp.ops.menu_func_export,
        'enable_object_export',
        obj.exp.ops.XRAY_OT_export_object.bl_idname,
        'Source Object (.object)'
    ),
    (
        anm.ops.menu_func_export,
        'enable_anm_export',
        anm.ops.XRAY_OT_export_anm.bl_idname,
        'Animation (.anm)'
    ),
    (
        skl.ops.menu_func_export,
        'enable_skls_export',
        skl.ops.XRAY_OT_export_skls.bl_idname,
        'Skeletal Animation (.skls)'
    ),
    (
        bones.ops.menu_func_export,
        'enable_bones_export',
        bones.ops.XRAY_OT_export_bones.bl_idname,
        'Bones Data (.bones)'
    ),
    (
        ogf.ops.menu_func_export,
        'enable_ogf_export',
        ogf.ops.XRAY_OT_export_ogf.bl_idname,
        'Game Object (.ogf)'
    ),
    (
        details.ops.menu_func_export,
        'enable_details_export',
        details.ops.XRAY_OT_export_details.bl_idname,
        'Level Details (.details)'
    ),
    (
        dm.ops.menu_func_export,
        'enable_dm_export',
        dm.ops.XRAY_OT_export_dm.bl_idname,
        'Detail Model (.dm)'
    ),
    (
        scene.ops.menu_func_export,
        'enable_level_export',
        scene.ops.XRAY_OT_export_scene_selection.bl_idname,
        'Scene Selection (.level)'
    ),
    (
        omf.ops.menu_func_export,
        'enable_omf_export',
        omf.ops.XRAY_OT_export_omf.bl_idname,
        'Game Motion (.omf)'
    ),
    (
        level.ops.menu_func_export,
        'enable_game_level_export',
        level.ops.XRAY_OT_export_level.bl_idname,
        'Game Level (level)'
    )
]


def remove_draw_functions(funct_list, menu):
    for draw_function, _, _, _ in funct_list:
        menu.remove(draw_function)


def append_draw_functions(funct_list, menu):
    preferences = version_utils.get_preferences()
    for draw_function, enable_prop, _, _ in funct_list:
        enable = getattr(preferences, enable_prop)
        if enable:
            menu.append(draw_function)


def append_menu_func():
    preferences = version_utils.get_preferences()
    import_menu, export_menu = version_utils.get_import_export_menus()

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
    XRAY_MT_import,
    XRAY_MT_export
)


def register():
    icons.register()
    details.register()
    skls_browser.register()
    props.register()

    for clas in classes:
        bpy.utils.register_class(clas)
    plugin_prefs.register()

    obj.imp.ops.register()
    obj.exp.ops.register()
    anm.ops.register()
    dm.ops.register()
    bones.ops.register()
    ogf.ops.register()
    skl.ops.register()
    omf.ops.register()
    scene.ops.register()
    level.ops.register()
    err.ops.register()
    append_menu_func()
    overlay_view_3d.__handle = bpy.types.SpaceView3D.draw_handler_add(
        overlay_view_3d, (),
        'WINDOW', 'POST_VIEW'
    )
    bpy.app.handlers.load_post.append(load_post)
    version_utils.get_scene_update_post().append(scene_update_post)
    hotkeys.register()
    edit_helpers.register()
    ops.register()
    ui.register()


def unregister():
    ui.unregister()
    ops.unregister()
    edit_helpers.unregister()
    hotkeys.unregister()
    err.ops.unregister()
    dm.ops.unregister()
    bones.ops.unregister()
    ogf.ops.unregister()
    level.ops.unregister()
    scene.ops.unregister()
    omf.ops.unregister()
    skl.ops.unregister()
    anm.ops.unregister()
    obj.exp.ops.unregister()
    obj.imp.ops.unregister()

    version_utils.get_scene_update_post().remove(scene_update_post)
    bpy.app.handlers.load_post.remove(load_post)
    bpy.types.SpaceView3D.draw_handler_remove(overlay_view_3d.__handle, 'WINDOW')

    import_menu, export_menu = version_utils.get_import_export_menus()

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
