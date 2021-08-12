# blender modules
import bpy

# addon modules
from . import ui
from . import icons
from . import version_utils

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


def menu_func_xray_import(self, _context):
    icon = icons.get_stalker_icon()
    self.layout.menu(XRAY_MT_import.bl_idname, icon_value=icon)


def menu_func_xray_export(self, _context):
    icon = icons.get_stalker_icon()
    self.layout.menu(XRAY_MT_export.bl_idname, icon_value=icon)


def append_draw_functions(funct_list, menu):
    preferences = version_utils.get_preferences()
    for draw_function, enable_prop, _, _ in funct_list:
        enable = getattr(preferences, enable_prop)
        if enable:
            menu.append(draw_function)


def remove_draw_functions(funct_list, menu):
    for draw_function, _, _, _ in funct_list:
        menu.remove(draw_function)


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


classes = (
    XRAY_MT_import,
    XRAY_MT_export
)


def register():
    for clas in classes:
        bpy.utils.register_class(clas)
    append_menu_func()


def unregister():
    import_menu, export_menu = version_utils.get_import_export_menus()

    # remove import menus
    remove_draw_functions(import_draw_functions, import_menu)
    # remove export menus
    remove_draw_functions(export_draw_functions, export_menu)
    # remove compact menus
    import_menu.remove(menu_func_xray_import)
    export_menu.remove(menu_func_xray_export)

    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
