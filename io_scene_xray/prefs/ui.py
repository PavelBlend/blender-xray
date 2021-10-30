from . import ops
from . import props
from .. import version_utils


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
