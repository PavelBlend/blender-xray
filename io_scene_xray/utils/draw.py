# blender modules
import bpy
import gpu

# addon modules
from . import version
from .. import text

if not version.IS_34:
    import bgl


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
        operators=None,
        operators_props=None,
        message_props=None
    ):

    message = text.get_text(message_text).capitalize()

    message_type = text.get_text(message_type).capitalize()
    if message_props:
        message_type = '{0}: {1}'.format(message_type, message_props)

    def show_message_menu(self, context):
        if elements:
            self.layout.label(text=message + ':')
        else:
            if message_text:
                self.layout.label(text=message + '.')
        for element in elements:
            self.layout.label(text=' ' * 4 + element)
        if operators:
            self.layout.operator_context = 'INVOKE_DEFAULT'
            for op_index, operator in enumerate(operators):
                op = self.layout.operator(operator)
                op.processed = True
                if operators_props:
                    operator_props = operators_props[op_index]
                    for prop_name, prop_value in operator_props.items():
                        setattr(op, prop_name, prop_value)

    if not bpy.app.background:
        bpy.context.window_manager.popup_menu(
            show_message_menu,
            title=message_type,
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


def redraw_areas():
    for area in bpy.context.window.screen.areas:
        area.tag_redraw()


def get_shader():
    name = 'UNIFORM_COLOR'
    if not version.IS_34:
        name = '3D_' + name
    shader = gpu.shader.from_builtin(name)
    return shader


def set_gl_line_width(width):
    if version.IS_34:
        gpu.state.line_width_set(width)
    else:
        bgl.glLineWidth(width)


def get_gl_line_width():
    if version.IS_34:
        prev_line_width = gpu.state.line_width_get()
    else:
        prev_line_width = bgl.Buffer(bgl.GL_FLOAT, [1])
        bgl.glGetFloatv(bgl.GL_LINE_WIDTH, prev_line_width)
        prev_line_width = prev_line_width[0]
    return prev_line_width


def set_gl_blend_mode():
    if version.IS_34:
        gpu.state.blend_set('ALPHA')
    else:
        bgl.glEnable(bgl.GL_BLEND)
