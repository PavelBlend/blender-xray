import bpy
from io_scene_xray import registry


@registry.module_thing
class _ListOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.list'
    bl_label = ''

    oper = bpy.props.StringProperty()
    collection = bpy.props.StringProperty()
    index = bpy.props.StringProperty()

    def execute(self, context):
        data = getattr(context, _ListOp.bl_idname + '.data')
        collection = getattr(data, self.collection)
        index = getattr(data, self.index)
        if self.oper == 'add':
            collection.add().name = '...'
        elif self.oper == 'del':
            collection.remove(index)
            if index > 0:
                setattr(data, self.index, index - 1)
        elif self.oper == 'mup':
            collection.move(index, index - 1)
            setattr(data, self.index, index - 1)
        elif self.oper == 'mdown':
            collection.move(index, index + 1)
            setattr(data, self.index, index + 1)
        return {'FINISHED'}


def draw_list_ops(layout, dataptr, propname, active_propname):
    def oper(oper, icon, enabled=None):
        lay = layout
        if (enabled is not None) and (not enabled):
            lay = lay.split(align=True)
            lay.enabled = False
        oper = lay.operator(_ListOp.bl_idname, icon=icon)
        oper.oper = oper
        oper.collection = propname
        oper.index = active_propname

    layout.context_pointer_set(_ListOp.bl_idname + '.data', dataptr)
    oper('add', 'ZOOMIN')
    collection = getattr(dataptr, propname)
    index = getattr(dataptr, active_propname)
    oper('del', 'ZOOMOUT', enabled=(index >= 0) and (index < len(collection)))
    oper('mup', 'TRIA_UP', enabled=(index > 0) and (index < len(collection)))
    oper('mdown', 'TRIA_DOWN', enabled=(index >= 0) and (index < len(collection) - 1))
