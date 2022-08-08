# blender modules
import bpy

# addon modules
from .. import utils


_collaps_op_props = {
    'key': bpy.props.StringProperty(),
}


class XRAY_OT_collaps(bpy.types.Operator):
    bl_idname = 'io_scene_xray.collaps'
    bl_label = ''
    bl_description = 'Show / hide UI block'

    if not utils.version.IS_28:
        for prop_name, prop_value in _collaps_op_props.items():
            exec('{0} = _collaps_op_props.get("{0}")'.format(prop_name))

    _DATA = {}

    @classmethod
    def get(cls, key):
        return cls._DATA.get(key, False)

    @classmethod
    def set_value(cls, key, value):
        cls._DATA[key] = value

    def execute(self, context):
        XRAY_OT_collaps._DATA[self.key] = not XRAY_OT_collaps.get(self.key)
        return {'FINISHED'}


def draw(layout, key, text=None, enabled=None, icon=None, style=None):
    col = layout.column(align=True)
    row = col.row(align=True)
    if (enabled is not None) and (not enabled):
        row_operator = row.row(align=True)
        row_operator.enabled = False
    else:
        row_operator = row
    isshow = XRAY_OT_collaps.get(key)
    if icon is None:
        icon = 'TRIA_DOWN' if isshow else 'TRIA_RIGHT'
    kwargs = {}
    if text is not None:
        kwargs['text'] = text
    box = None
    if isshow:
        box = col
        if style != 'nobox':
            box = box.box()
    if style == 'tree':
        row.alignment = 'LEFT'
        row = row_operator.row()
        if box:
            bxr = box.row(align=True)
            bxr.alignment = 'LEFT'
            bxr.label(text='')
            box = bxr.column()
    oper = row_operator.operator(XRAY_OT_collaps.bl_idname, icon=icon, emboss=style != 'tree', **kwargs)
    oper.key = key
    return row, box


def is_opened(key):
    return XRAY_OT_collaps.get(key)


def register():
    utils.version.assign_props([(_collaps_op_props, XRAY_OT_collaps), ])
    bpy.utils.register_class(XRAY_OT_collaps)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_collaps)
