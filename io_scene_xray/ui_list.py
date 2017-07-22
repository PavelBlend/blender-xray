import bpy
from . import registry


@registry.module_thing
class _ListOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.list'
    bl_label = ''

    op = bpy.props.StringProperty()
    collection = bpy.props.StringProperty()
    index = bpy.props.StringProperty()

    def execute(self, context):
        data = getattr(context, _ListOp.bl_idname + '.data')
        collection = getattr(data, self.collection)
        index = getattr(data, self.index)
        if self.op == 'add':
            collection.add().name = '...'
        elif self.op == 'del':
            collection.remove(index)
            if index > 0:
                setattr(data, self.index, index - 1)
        elif self.op == 'mup':
            collection.move(index, index - 1)
            setattr(data, self.index, index - 1)
        elif self.op == 'mdown':
            collection.move(index, index + 1)
            setattr(data, self.index, index + 1)
        return {'FINISHED'}


def draw_list_ops(layout, dataptr, propname, active_propname):
    def op(op, icon, enabled=None):
        l = layout
        if (enabled is not None) and (not enabled):
            l = l.split(align=True)
            l.enabled = False
        oper = l.operator(_ListOp.bl_idname, icon=icon)
        oper.op = op
        oper.collection = propname
        oper.index = active_propname

    layout.context_pointer_set(_ListOp.bl_idname + '.data', dataptr)
    op('add', 'ZOOMIN')
    collection = getattr(dataptr, propname)
    index = getattr(dataptr, active_propname)
    op('del', 'ZOOMOUT', enabled=(index >= 0) and (index < len(collection)))
    op('mup', 'TRIA_UP', enabled=(index > 0) and (index < len(collection)))
    op('mdown', 'TRIA_DOWN', enabled=(index >= 0) and (index < len(collection) - 1))
