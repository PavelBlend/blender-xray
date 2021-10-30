# blender modules
import rna_keymap_ui

# addon modules
from . import ops
from . import props
from .. import version_utils
from .. import hotkeys


path_props_names = {
    'fs_ltx_file': 'FS Ltx File',
    'gamedata_folder': 'Gamedata Folder',
    'textures_folder': 'Textures Folder',
    'gamemtl_file': 'Game Materials File',
    'eshader_file': 'Engine Shaders File',
    'cshader_file': 'Compile Shaders File',
    'objects_folder': 'Objects Folder'
}


def get_split(layout):
    return version_utils.layout_split(layout, 0.3)


def draw_path_prop(prefs, prop):
    layout = prefs.layout
    split = get_split(layout)
    split.label(text=path_props_names[prop] + ':')
    auto_prop = props.build_auto_id(prop)
    if getattr(prefs, auto_prop) and not getattr(prefs, prop):
        row = split.row(align=True)
        row_prop = row.row(align=True)
        row_prop.enabled = False
        row_prop.prop(prefs, auto_prop, text='')
        operator = row.operator(
            ops.XRAY_OT_explicit_path.bl_idname,
            icon='MODIFIER',
            text=''
        )
        operator.path = prop
    else:
        split.prop(prefs, prop, text='')


def draw_paths(prefs):
    layout = prefs.layout
    split = get_split(layout)
    split.label(text=path_props_names['fs_ltx_file'] + ':')
    split.prop(prefs, 'fs_ltx_file', text='')
    draw_path_prop(prefs, 'gamedata_folder')
    draw_path_prop(prefs, 'textures_folder')
    draw_path_prop(prefs, 'gamemtl_file')
    draw_path_prop(prefs, 'eshader_file')
    draw_path_prop(prefs, 'cshader_file')
    draw_path_prop(prefs, 'objects_folder')


def draw_operators_enable_disable(prefs):
    layout = prefs.layout
    row = layout.row()
    # import operators
    column_import = row.column()
    column_import.label(text='Import Operators:')
    column_import.prop(prefs, 'enable_object_import', text='*.object')
    column_import.prop(prefs, 'enable_anm_import', text='*.anm')
    column_import.prop(prefs, 'enable_dm_import', text='*.dm')
    column_import.prop(prefs, 'enable_details_import', text='*.details')
    column_import.prop(prefs, 'enable_skls_import', text='*.skls')
    column_import.prop(prefs, 'enable_bones_import', text='*.bones')
    column_import.prop(prefs, 'enable_level_import', text='*.level')
    column_import.prop(prefs, 'enable_omf_import', text='*.omf')
    column_import.prop(prefs, 'enable_game_level_import', text='level')
    column_import.prop(prefs, 'enable_ogf_import', text='*.ogf')
    column_import.prop(prefs, 'enable_err_import', text='*.err')
    # export operators
    column_export = row.column()
    column_export.label(text='Export Operators:')
    column_export.prop(prefs, 'enable_object_export', text='*.object')
    column_export.prop(prefs, 'enable_anm_export', text='*.anm')
    column_export.prop(prefs, 'enable_dm_export', text='*.dm')
    column_export.prop(prefs, 'enable_details_export', text='*.details')
    column_export.prop(prefs, 'enable_skls_export', text='*.skls')
    column_export.prop(prefs, 'enable_bones_export', text='*.bones')
    column_export.prop(prefs, 'enable_level_export', text='*.level')
    column_export.prop(prefs, 'enable_omf_export', text='*.omf')
    column_export.prop(prefs, 'enable_game_level_export', text='level')
    column_export.prop(prefs, 'enable_ogf_export', text='*.ogf')


def draw_keymaps(context, prefs):
    layout = prefs.layout
    win_manager = context.window_manager
    keyconfig = win_manager.keyconfigs.user
    keymaps = keyconfig.keymaps.get('3D View')
    if keymaps:
        keymap_items = keymaps.keymap_items
        for operator, _, _, _, _ in hotkeys.keymap_items_list:
            row = layout.row(align=True)
            keymap = keymap_items.get(operator.bl_idname)
            if keymap:
                row.context_pointer_set('keymap', keymaps)
                rna_keymap_ui.draw_kmi(
                    ["ADDON", "USER", "DEFAULT"],
                    keyconfig, keymaps, keymap, row, 0
                )
            else:
                row.label(text=operator.bl_label)
                change_keymap_op = row.operator(
                    props.XRAY_OT_add_keymap.bl_idname,
                    text='Add'
                )
                change_keymap_op.operator = operator.bl_idname
