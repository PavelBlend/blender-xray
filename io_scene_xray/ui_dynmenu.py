import bpy
from . import registry


@registry.module_thing
class _DynamicMenuOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.dynmenu'
    bl_label = ''

    prop = bpy.props.StringProperty()
    value = bpy.props.StringProperty()

    def execute(self, context):
        data = getattr(context, _DynamicMenuOp.bl_idname + '.data')
        setattr(data, self.prop, self.value)
        return {'FINISHED'}


def _path_to_prefix(path):
    return _DynamicMenuOp.bl_idname + '.idx.' + '.'.join(map(str, path))


def _detect_current_path(context):
    result = []
    for _ in range(20):
        for i in range(100):
            pfx = _path_to_prefix(result + [i])
            if getattr(context, pfx, None) is None:
                if i:
                    result.append(i - 1)
                break
    return result


class DynamicMenu(bpy.types.Menu):
    bl_label = ''
    prop_name = '<prop>'

    @classmethod
    def items_for_path(cls, path):
        pfx = '/'.join(map(str, path))
        return [
            (pfx + '/0', None),
            (pfx + '/1', None),
            ('<text>', '<value>')
        ]

    def draw(self, context):
        layout = self.layout
        path = _detect_current_path(context)
        path_len = len(path)
        if path_len:
            pfx = _path_to_prefix(path[:-1] + [path[path_len - 1] + 1])  # next sibling
            layout.context_pointer_set(pfx, None)  # stop

        items = self.items_for_path(path)
        for i, item in enumerate(items):
            text, value = item
            pfx = _path_to_prefix(path + [i])
            layout.context_pointer_set(pfx, context)
            if isinstance(value, str):
                oper = layout.operator(_DynamicMenuOp.bl_idname, text=text)
                oper.prop = self.prop_name
                oper.value = value
            else:
                layout.menu(self.bl_idname, text=text)

        pfx = _path_to_prefix(path + [len(items)])  # after last child
        layout.context_pointer_set(pfx, None)  # stop

    @staticmethod
    def set_layout_context_data(layout, data):
        layout.context_pointer_set(_DynamicMenuOp.bl_idname + '.data', data)
