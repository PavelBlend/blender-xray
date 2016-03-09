import bpy


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
    for l in range(20):
        for i in range(100):
            s = _path_to_prefix(result + [i])
            if getattr(context, s, None) is None:
                if i:
                    result.append(i - 1)
                break
    return result


class DynamicMenu(bpy.types.Menu):
    bl_label = ''
    prop_name = '<prop>'

    @classmethod
    def items_for_path(cls, path):
        s = '/'.join(map(str, path))
        return [
            (s + '/0', None),
            (s + '/1', None),
            ('<text>', '<value>')
        ]

    def draw(self, context):
        layout = self.layout
        path = _detect_current_path(context)
        path_len = len(path)
        if path_len:
            s = _path_to_prefix(path[:-1] + [path[path_len - 1] + 1])  # next sibling
            layout.context_pointer_set(s, None)  # stop

        items = self.items_for_path(path)
        for i, e in enumerate(items):
            tx, vl = e
            s = _path_to_prefix(path + [i])
            layout.context_pointer_set(s, context)
            if isinstance(vl, str):
                op = layout.operator(_DynamicMenuOp.bl_idname, text=tx)
                op.prop = self.prop_name
                op.value = vl
            else:
                layout.menu(self.bl_idname, text=tx)

        s = _path_to_prefix(path + [i + 1])  # after last child
        layout.context_pointer_set(s, None)  # stop

    @staticmethod
    def set_layout_context_data(layout, data):
        layout.context_pointer_set(_DynamicMenuOp.bl_idname + '.data', data)


def register():
    bpy.utils.register_class(_DynamicMenuOp)


def unregister():
    bpy.utils.unregister_class(_DynamicMenuOp)
