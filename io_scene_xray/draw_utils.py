# addon modules
from . import version_utils


def draw_files_count(operator):
    row = operator.layout.row()
    row.enabled = False
    files_count = len(operator.files)
    if files_count == 1:
        if not operator.files[0].name:
            files_count = 0
    row.label(text='{} items'.format(files_count))


def draw_fmt_ver_prop(layout, owner, prop, lay_type='SPLIT', use_row=True):
    if lay_type == 'SPLIT':
        lay = version_utils.layout_split(layout, 0.5)
    elif lay_type == 'ROW':
        lay = layout.row()
    else:
        lay = layout.column()
    lay.label(text='Format Version:')
    if use_row:
        prop_lay = lay.row(align=True)
    else:
        prop_lay = lay.column(align=True)
    prop_lay.prop(owner, prop, expand=True)
