# blender modules
import bpy

# addon modules
from .. import utils


class XRAY_OT_list(bpy.types.Operator):
    bl_idname = 'io_scene_xray.list'
    bl_label = ''

    operation = bpy.props.StringProperty()
    collection = bpy.props.StringProperty()
    index = bpy.props.StringProperty()

    def execute(self, context):
        data = getattr(context, XRAY_OT_list.bl_idname + '.data')
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


def draw_list_ops(layout, dataptr, propname, active_propname, custom_elements_func=None):
    def operator(operation, icon, enabled=None):
        lay = layout
        if (enabled is not None) and (not enabled):
            lay = lay.row(align=True)
            lay.enabled = False
        operator = lay.operator(XRAY_OT_list.bl_idname, icon=icon)
        operator.operation = operation
        operator.collection = propname
        operator.index = active_propname

    layout.context_pointer_set(XRAY_OT_list.bl_idname + '.data', dataptr)
    operator('add', utils.version.get_icon('ZOOMIN'))
    collection = getattr(dataptr, propname)
    index = getattr(dataptr, active_propname)
    operator('remove', utils.version.get_icon('ZOOMOUT'), enabled=(index >= 0) and (index < len(collection)))
    operator('move_up', 'TRIA_UP', enabled=(index > 0) and (index < len(collection)))
    operator('move_down', 'TRIA_DOWN', enabled=(index >= 0) and (index < len(collection) - 1))
    if custom_elements_func:
        custom_elements_func(layout)


def register():
    utils.version.register_operators(XRAY_OT_list)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_list)
