# blender modules
import bpy

# addon modules
from .. import utils
from .. import formats


_dynamic_menu_op_props = {
    'prop': bpy.props.StringProperty(),
    'value': bpy.props.StringProperty(),
    'desc': bpy.props.StringProperty()
}


class XRAY_OT_dynamic_menu(bpy.types.Operator):
    bl_idname = 'io_scene_xray.dynmenu'
    bl_label = ''

    if not utils.version.IS_28:
        for prop_name, prop_value in _dynamic_menu_op_props.items():
            exec('{0} = _dynamic_menu_op_props.get("{0}")'.format(prop_name))

    @classmethod
    def description(self, context, properties):
        desc = getattr(properties, 'desc', '')
        return desc

    def execute(self, context):
        data = getattr(context, XRAY_OT_dynamic_menu.bl_idname + '.data')
        setattr(data, self.prop, self.value)
        return {'FINISHED'}


def _path_to_prefix(path):
    return XRAY_OT_dynamic_menu.bl_idname + '.idx.' + '.'.join(map(str, path))


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
            text, data = item
            pfx = _path_to_prefix(path + [i])
            layout.context_pointer_set(pfx, context)
            if isinstance(data, list):
                layout.menu(self.bl_idname, text=text)
            else:
                oper = layout.operator(XRAY_OT_dynamic_menu.bl_idname, text=text)
                oper.prop = self.prop_name
                value, desc = data
                oper.value = value
                oper.desc = desc

        pfx = _path_to_prefix(path + [len(items)])  # after last child
        layout.context_pointer_set(pfx, None)  # stop

    @staticmethod
    def set_layout_context_data(layout, data):
        layout.context_pointer_set(XRAY_OT_dynamic_menu.bl_idname + '.data', data)


class XRAY_MT_xr_template(DynamicMenu):
    @staticmethod
    def parse(data, fparse):
        def push_dict(dct, split, value, desc):
            if len(split) == 1:
                dct[split[0]] = (value, desc)
            else:
                nested = dct.get(split[0], None)
                if nested is None:
                    dct[split[0]] = nested = {}
                push_dict(nested, split[1:], value, desc)

        def dict_to_array(dct):
            result = []
            root_result = []
            for (key, item) in dct.items():
                if isinstance(item, dict):
                    result.append((key, dict_to_array(item)))
                else:
                    val, desc = item
                    root_result.append((key, (val, desc)))
            result = sorted(result, key=lambda e: e[0])
            root_result = sorted(root_result, key=lambda e: e[0])
            result.extend(root_result)
            return result

        tmp = {}
        for (name, desc, _) in fparse(data):
            split = name.split('\\')
            push_dict(tmp, split, name, desc)
        return dict_to_array(tmp)

    @classmethod
    def create_cached(cls, pref_prop, fparse):
        return formats.xr.create_cached_file_data(
            lambda: getattr(utils.version.get_preferences(), pref_prop, None),
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
    XRAY_OT_dynamic_menu,
    XRAY_MT_xr_template
)


def register():
    utils.version.assign_props([(_dynamic_menu_op_props, XRAY_OT_dynamic_menu), ])
    for operator in classes:
        bpy.utils.register_class(operator)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
