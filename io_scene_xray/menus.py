# blender modules
import bpy

# addon modules
from . import ui
from . import utils
from . import formats


# import operators: (operator, lebel)
import_ops = (
    (formats.obj.imp.ops.XRAY_OT_import_object, 'Object'),
    (formats.skl.ops.XRAY_OT_import_skls, 'Skls'),
    (formats.ogf.imp.ops.XRAY_OT_import_ogf, 'Ogf'),
    (formats.omf.ops.XRAY_OT_import_omf, 'Omf'),
    (formats.anm.ops.XRAY_OT_import_anm, 'Anm'),
    (formats.bones.ops.XRAY_OT_import_bones, 'Bones'),
    (formats.dm.ops.XRAY_OT_import_dm, 'Dm'),
    (formats.details.ops.XRAY_OT_import_details, 'Details'),
    (formats.scene.ops.XRAY_OT_import_scene_selection, 'Scene'),
    (formats.level.ops.XRAY_OT_import_level, 'Level'),
    (formats.part.ops.XRAY_OT_import_part, 'Part'),
    (formats.err.ops.XRAY_OT_import_err, 'Err')
)

# export operators: (operator, lebel)
export_ops = (
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
)


def _draw_xray_menu(self, menu):    # pragma: no cover
    icon = ui.icons.get_stalker_icon()
    self.layout.menu(menu.bl_idname, icon_value=icon)


def _draw_xray_menu_import(self, context):    # pragma: no cover
    _draw_xray_menu(self, XRAY_MT_import)


def _draw_xray_menu_export(self, context):    # pragma: no cover
    _draw_xray_menu(self, XRAY_MT_export)


def get_enabled_operators(ops_list, mode):
    preferences = utils.version.get_preferences()
    operators = []
    for operator, label in ops_list:
        enable_name = 'enable_{0}_{1}'.format(label.lower(), mode)
        enable_value = getattr(preferences, enable_name)
        if enable_value:
            operators.append(operator)
    return operators


def _append_standart_draw_functions(ops_list, menu, mode):
    operators = get_enabled_operators(ops_list, mode)
    for operator in operators:
        draw_function = utils.ie.get_draw_fun(operator)
        menu.append(draw_function)


def _append_compact_draw_functions(ops_list, menu, mode, draw):
    operators = get_enabled_operators(ops_list, mode)
    if operators:
        menu.prepend(draw)


def _remove_draw_functions(ops_list, menu):
    for operator, label in ops_list:
        draw_function = getattr(operator, 'draw_fun', None)
        if draw_function:
            menu.remove(draw_function)


def _remove_ops_from_menus(menu_imp, menu_exp):
    # remove operators from import menu
    _remove_draw_functions(import_ops, menu_imp)

    # remove operators from export menu
    _remove_draw_functions(export_ops, menu_exp)

    # remove compact menus
    menu_imp.remove(_draw_xray_menu_import)
    menu_exp.remove(_draw_xray_menu_export)


def append_menu_func():
    preferences = utils.version.get_preferences()
    menu_imp, menu_exp = utils.version.get_import_export_menus()

    _remove_ops_from_menus(menu_imp, menu_exp)

    # create compact menus
    if preferences.compact_menus:
        _append_compact_draw_functions(
            import_ops,
            menu_imp,
            'import',
            _draw_xray_menu_import
        )
        _append_compact_draw_functions(
            export_ops,
            menu_exp,
            'export',
            _draw_xray_menu_export
        )

    # create standart menus
    else:
        _append_standart_draw_functions(import_ops, menu_imp, 'import')
        _append_standart_draw_functions(export_ops, menu_exp, 'export')


class XRayBaseMenu(bpy.types.Menu):
    bl_label = ui.base.build_label()

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        operators = get_enabled_operators(self.ops_list, self.mode)
        for operator in operators:
            text = utils.draw.build_op_label(operator, compact=True)
            layout.operator(operator.bl_idname, text=text)


class XRAY_MT_import(XRayBaseMenu):
    bl_idname = 'XRAY_MT_import'

    ops_list = import_ops
    mode = 'import'


class XRAY_MT_export(XRayBaseMenu):
    bl_idname = 'XRAY_MT_export'

    ops_list = export_ops
    mode = 'export'


classes = (
    XRAY_MT_import,
    XRAY_MT_export
)


def register():
    for clas in classes:
        bpy.utils.register_class(clas)

    append_menu_func()


def unregister():
    menu_imp, menu_exp = utils.version.get_import_export_menus()

    _remove_ops_from_menus(menu_imp, menu_exp)

    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
