import bpy

from io_scene_xray import registry

class _CollapsOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.collaps'
    bl_label = ''
    bl_description = 'Show / hide UI block'

    key = bpy.props.StringProperty()

    _DATA = {}

    @classmethod
    def get(cls, key):
        return cls._DATA.get(key, False)

    def execute(self, _context):
        _CollapsOp._DATA[self.key] = not _CollapsOp.get(self.key)
        return {'FINISHED'}


def draw(layout, key, text=None, enabled=None, icon=None, style=None):
    col = layout.column(align=True)
    row = col.row(align=True)
    if (enabled is not None) and (not enabled):
        row = row.row(align=True)
        row.enabled = False
    isshow = _CollapsOp.get(key)
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
        row = row.row()
        row.alignment = 'LEFT'
        if box:
            bxr = box.row(align=True)
            bxr.alignment = 'LEFT'
            bxr.label('')
            box = bxr.column()
    oper = row.operator(_CollapsOp.bl_idname, icon=icon, emboss=style != 'tree', **kwargs)
    oper.key = key
    return row, box

def is_opened(key):
    return _CollapsOp.get(key)

registry.module_requires(__name__, [
    _CollapsOp,
])
