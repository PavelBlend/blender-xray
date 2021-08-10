import bpy

from ..utils import create_cached_file_data
from ..version_utils import assign_props, IS_28, get_preferences


_dynamic_menu_op_props = {
    'prop': bpy.props.StringProperty(),
    'value': bpy.props.StringProperty()
}


class _DynamicMenuOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.dynmenu'
    bl_label = ''

    if not IS_28:
        for prop_name, prop_value in _dynamic_menu_op_props.items():
            exec('{0} = _dynamic_menu_op_props.get("{0}")'.format(prop_name))

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
    bl_idname = 'XRAY_MT_DynamicMenu'
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


class XRayXrMenuTemplate(DynamicMenu):
    @staticmethod
    def parse(data, fparse):
        def push_dict(dct, split, value):
            if len(split) == 1:
                dct[split[0]] = value
            else:
                nested = dct.get(split[0], None)
                if nested is None:
                    dct[split[0]] = nested = dict()
                push_dict(nested, split[1:], value)

        def dict_to_array(dct):
            result = []
            root_result = []
            for (key, val) in dct.items():
                if isinstance(val, str):
                    root_result.append((key, val))
                else:
                    result.append((key, dict_to_array(val)))
            result = sorted(result, key=lambda e: e[0])
            root_result = sorted(root_result, key=lambda e: e[0])
            result.extend(root_result)
            return result

        tmp = dict()
        for (name, _, _) in fparse(data):
            split = name.split('\\')
            push_dict(tmp, split, name)
        return dict_to_array(tmp)

    @classmethod
    def create_cached(cls, pref_prop, fparse):
        return create_cached_file_data(
            lambda: getattr(get_preferences(), pref_prop, None),
            lambda data: cls.parse(data, fparse)
        )

    @classmethod
    def items_for_path(cls, path):
        data = cls.cached()
        if data is None:
            return []
        for pth in path:
            data = data[pth][1]
        return data


classes = (
    _DynamicMenuOp,
    XRayXrMenuTemplate
)


def register():
    assign_props([(_dynamic_menu_op_props, _DynamicMenuOp), ])
    for operator in classes:
        bpy.utils.register_class(operator)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
