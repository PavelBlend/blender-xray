# blender modules
import bpy

# addon modules
from . import version
from .. import text


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
        lay = version.layout_split(layout, 0.5)
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


def show_message(
        message_text,
        elements,
        message_type,
        icon,
        operator=None,
        operator_props=None
    ):

    message = text.get_text(message_text).capitalize()

    def show_message_menu(self, context):
        if elements:
            self.layout.label(text=message + ':')
        else:
            self.layout.label(text=message + '.')
        for element in elements:
            self.layout.label(text=' ' * 4 + element)
        if operator:
            op = self.layout.operator(operator)
            for prop_name, prop_value in operator_props.items():
                setattr(op, prop_name, prop_value)

    if not bpy.app.background:
        bpy.context.window_manager.popup_menu(
            show_message_menu,
            title=message_type.capitalize(),
            icon=icon
        )


def build_op_label(operator, compact=False):
    # build operator label
    if compact:
        prefix = ''
    else:
        prefix = 'X-Ray '
    label = '{0}{1} ({2})'.format(prefix, operator.text, operator.ext)
    return label


def draw_presets(layout, menu, op_add):
    row = layout.row(align=True)
    row.menu(menu.__name__, text=menu.bl_label)
    row.operator(
        op_add.bl_idname,
        text='',
        icon=version.get_icon('ZOOMIN')
    )
    row.operator(
        op_add.bl_idname,
        text='',
        icon=version.get_icon('ZOOMOUT')
    ).remove_active = True
