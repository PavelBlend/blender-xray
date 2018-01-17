import bpy
from io_scene_xray import registry


@registry.module_thing
class _ListOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.list'
    bl_label = ''

    operation = bpy.props.StringProperty()
    collection = bpy.props.StringProperty()
    index = bpy.props.StringProperty()

    def execute(self, context):
        data = getattr(context, _ListOp.bl_idname + '.data')
        collection = getattr(data, self.collection)
        index = getattr(data, self.index)
        if self.operation == 'add':
            collection.add().name = '...'
        elif self.operation == 'remove':
            collection.remove(index)
            if index > 0:
                setattr(data, self.index, index - 1)
        elif self.operation == 'move_up':
            collection.move(index, index - 1)
            setattr(data, self.index, index - 1)
        elif self.operation == 'move_down':
            collection.move(index, index + 1)
            setattr(data, self.index, index + 1)
        return {'FINISHED'}


def draw_list_ops(layout, dataptr, propname, active_propname):
    def operator(operation, icon, enabled=None):
        lay = layout
        if (enabled is not None) and (not enabled):
            lay = lay.split(align=True)
            lay.enabled = False
        operator = lay.operator(_ListOp.bl_idname, icon=icon)
        operator.operation = operation
        operator.collection = propname
        operator.index = active_propname

    layout.context_pointer_set(_ListOp.bl_idname + '.data', dataptr)
    operator('add', 'ZOOMIN')
    collection = getattr(dataptr, propname)
    index = getattr(dataptr, active_propname)
    operator('remove', 'ZOOMOUT', enabled=(index >= 0) and (index < len(collection)))
    operator('move_up', 'TRIA_UP', enabled=(index > 0) and (index < len(collection)))
    operator('move_down', 'TRIA_DOWN', enabled=(index >= 0) and (index < len(collection) - 1))
