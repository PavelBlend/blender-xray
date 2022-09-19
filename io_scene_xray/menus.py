# blender modules
import bpy

# addon modules
from . import ui
from . import utils
from . import formats


# import operators: (operator, lebel)
import_ops = [
    (formats.obj.imp.ops.XRAY_OT_import_object, 'Object'),
    (formats.skl.ops.XRAY_OT_import_skls, 'Skls'),
    (formats.ogf.ops.XRAY_OT_import_ogf, 'Ogf'),
    (formats.omf.ops.XRAY_OT_import_omf, 'Omf'),
    (formats.anm.ops.XRAY_OT_import_anm, 'Anm'),
    (formats.bones.ops.XRAY_OT_import_bones, 'Bones'),
    (formats.dm.ops.XRAY_OT_import_dm, 'Dm'),
    (formats.details.ops.XRAY_OT_import_details, 'Details'),
    (formats.scene.ops.XRAY_OT_import_scene_selection, 'Scene'),
    (formats.level.ops.XRAY_OT_import_level, 'Level'),
    (formats.part.ops.XRAY_OT_import_part, 'Part'),
    (formats.err.ops.XRAY_OT_import_err, 'Err')
]

# export operators: (operator, lebel)
export_ops = [
    (formats.obj.exp.ops.XRAY_OT_export_object, 'Object'),
    (formats.skl.ops.XRAY_OT_export_skls, 'Skls'),
    (formats.skl.ops.XRAY_OT_export_skl_batch, 'Skl'),
    (formats.ogf.ops.XRAY_OT_export_ogf, 'Ogf'),
    (formats.omf.ops.XRAY_OT_export_omf, 'Omf'),
    (formats.anm.ops.XRAY_OT_export_anm, 'Anm'),
    (formats.bones.ops.XRAY_OT_export_bones, 'Bones'),
    (formats.dm.ops.XRAY_OT_export_dm, 'Dm'),
    (formats.details.ops.XRAY_OT_export_details, 'Details'),
    (formats.scene.ops.XRAY_OT_export_scene_selection, 'Scene'),
    (formats.level.ops.XRAY_OT_export_level, 'Level')
]


def menu_func_xray_import(self, context):
    icon = ui.icons.get_stalker_icon()
    self.layout.menu(XRAY_MT_import.bl_idname, icon_value=icon)


def menu_func_xray_export(self, context):
    icon = ui.icons.get_stalker_icon()
    self.layout.menu(XRAY_MT_export.bl_idname, icon_value=icon)


def append_draw_functions(ops_list, menu, mode):
    preferences = utils.version.get_preferences()
    for operator, label in ops_list:
        enable_prop = 'enable_{0}_{1}'.format(label.lower(), mode)
        enable = getattr(preferences, enable_prop)
        if enable:
            draw_function = utils.ie.get_draw_fun(operator)
            menu.append(draw_function)


def remove_draw_functions(ops_list, menu):
    for operator, label in ops_list:
        if hasattr(operator, 'draw_fun'):
            draw_function = operator.draw_fun
            menu.remove(draw_function)


def get_enabled_operators(ops_list, mode):
    preferences = utils.version.get_preferences()
    operators = []
    for operator, label in ops_list:
        enable_prop = 'enable_{0}_{1}'.format(label.lower(), mode)
        enable = getattr(preferences, enable_prop)
        if enable:
            id_name = operator.bl_idname
            text = utils.draw.build_op_label(operator, compact=True)
            operators.append((id_name, text))
    return operators


def append_menu_func():
    preferences = utils.version.get_preferences()
    import_menu, export_menu = utils.version.get_import_export_menus()

    # remove import menus
    remove_draw_functions(import_ops, import_menu)
    # remove export menus
    remove_draw_functions(export_ops, export_menu)
    # remove compact menus
    import_menu.remove(menu_func_xray_import)
    export_menu.remove(menu_func_xray_export)

    if preferences.compact_menus:
        # create compact import menus
        enabled_imp_ops = get_enabled_operators(import_ops, 'import')
        if enabled_imp_ops:
            import_menu.prepend(menu_func_xray_import)
        # create compact export menus
        enabled_exp_ops = get_enabled_operators(export_ops, 'export')
        if enabled_exp_ops:
            export_menu.prepend(menu_func_xray_export)
    else:
        # create standart import menus
        append_draw_functions(import_ops, import_menu, 'import')
        # create standart export menus
        append_draw_functions(export_ops, export_menu, 'export')


class XRAY_MT_import(bpy.types.Menu):
    bl_idname = 'XRAY_MT_import'
    bl_label = ui.base.build_label()

    def draw(self, context):
        layout = self.layout
        import_operators = get_enabled_operators(import_ops, 'import')
        for id_name, text in import_operators:
            layout.operator(id_name, text=text)


class XRAY_MT_export(bpy.types.Menu):
    bl_idname = 'XRAY_MT_export'
    bl_label = ui.base.build_label()

    def draw(self, context):
        layout = self.layout
        export_operators = get_enabled_operators(export_ops, 'export')
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
    import_menu, export_menu = utils.version.get_import_export_menus()

    # remove import menus
    remove_draw_functions(import_ops, import_menu)
    # remove export menus
    remove_draw_functions(export_ops, export_menu)
    # remove compact menus
    import_menu.remove(menu_func_xray_import)
    export_menu.remove(menu_func_xray_export)

    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
