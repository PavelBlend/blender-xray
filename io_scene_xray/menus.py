# blender modules
import bpy

# addon modules
from . import ui
from . import icons
from . import utils
from . import ie_utils
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
from . import part


# import draw functions
import_draw_functions = [
    ('enable_object_import', obj.imp.ops.XRAY_OT_import_object, 'Object'),
    ('enable_skls_import', skl.ops.XRAY_OT_import_skls, 'Skls'),
    ('enable_ogf_import', ogf.ops.XRAY_OT_import_ogf, 'Ogf'),
    ('enable_omf_import', omf.ops.XRAY_OT_import_omf, 'Omf'),
    ('enable_anm_import', anm.ops.XRAY_OT_import_anm, 'Anm'),
    ('enable_bones_import', bones.ops.XRAY_OT_import_bones, 'Bones'),
    ('enable_dm_import',dm.ops.XRAY_OT_import_dm, 'Dm'),
    ('enable_details_import', details.ops.XRAY_OT_import_details, 'Details'),
    ('enable_level_import', scene.ops.XRAY_OT_import_scene_selection, 'Scene'),
    ('enable_game_level_import', level.ops.XRAY_OT_import_level, 'Level'),
    ('enable_part_import', part.ops.XRAY_OT_import_part, 'Part'),
    ('enable_err_import', err.ops.XRAY_OT_import_err, 'Err')
]

# export draw functions
export_draw_functions = [
    ('enable_object_export', obj.exp.ops.XRAY_OT_export_object, 'Object'),
    ('enable_skls_export', skl.ops.XRAY_OT_export_skls, 'Skls'),
    ('enable_skl_export', skl.ops.XRAY_OT_export_skl_batch, 'Skl'),
    ('enable_ogf_export', ogf.ops.XRAY_OT_export_ogf, 'Ogf'),
    ('enable_omf_export', omf.ops.XRAY_OT_export_omf, 'Omf'),
    ('enable_anm_export', anm.ops.XRAY_OT_export_anm, 'Anm'),
    ('enable_bones_export', bones.ops.XRAY_OT_export_bones, 'Bones'),
    ('enable_dm_export', dm.ops.XRAY_OT_export_dm, 'Dm'),
    ('enable_details_export', details.ops.XRAY_OT_export_details, 'Details'),
    ('enable_level_export', scene.ops.XRAY_OT_export_scene_selection, 'Scene'),
    ('enable_game_level_export', level.ops.XRAY_OT_export_level, 'Level')
]


def menu_func_xray_import(self, context):
    icon = icons.get_stalker_icon()
    self.layout.menu(XRAY_MT_import.bl_idname, icon_value=icon)


def menu_func_xray_export(self, context):
    icon = icons.get_stalker_icon()
    self.layout.menu(XRAY_MT_export.bl_idname, icon_value=icon)


def append_draw_functions(ops_list, menu):
    preferences = version_utils.get_preferences()
    for enable_prop, operator, label in ops_list:
        enable = getattr(preferences, enable_prop)
        if enable:
            draw_function = ie_utils.get_draw_fun(operator)
            menu.append(draw_function)


def remove_draw_functions(ops_list, menu):
    for enable, operator, label in ops_list:
        if hasattr(operator, 'draw_fun'):
            draw_function = operator.draw_fun
            menu.remove(draw_function)


def get_enabled_operators(ops_list):
    preferences = version_utils.get_preferences()
    operators = []
    for enable_prop, operator, label in ops_list:
        enable = getattr(preferences, enable_prop)
        if enable:
            id_name = operator.bl_idname
            text = utils.build_op_label(operator, compact=True)
            operators.append((id_name, text))
    return operators


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
