# standart modules
import contextlib

# blender modules
import bpy


def is_blender_2_77():
    if bpy.app.version[0] == 2 and bpy.app.version[1] <= 77:
        return True
    else:
        return False


def is_blender_2_80():
    return bpy.app.version >= (2, 80, 0)


def is_blender_2_81():
    if bpy.app.version[0] == 2 and bpy.app.version[1] >= 81:
        return True
    else:
        return False


def is_blender_2_93():
    if bpy.app.version[0] == 2 and bpy.app.version[1] >= 93:
        return True
    else:
        return False


IS_277 = is_blender_2_77()
IS_28 = is_blender_2_80()
IS_281 = is_blender_2_81()
IS_293 = is_blender_2_93()


def get_import_export_menus():
    if IS_28:
        import_menu = bpy.types.TOPBAR_MT_file_import
        export_menu = bpy.types.TOPBAR_MT_file_export
    else:
        import_menu = bpy.types.INFO_MT_file_import
        export_menu = bpy.types.INFO_MT_file_export
    return import_menu, export_menu


def get_scene_update_post():
    if IS_28:
        scene_update_post = bpy.app.handlers.depsgraph_update_post
    else:
        scene_update_post = bpy.app.handlers.scene_update_post
    return scene_update_post


ICONS_279_TO_280 = {
    'ZOOMIN': 'ADD',
    'ZOOMOUT': 'REMOVE',
    'BBOX': 'SHADING_BBOX',
    'VISIBLE_IPO_ON': 'HIDE_OFF',
    'BUTS': 'PROPERTIES'
}


def get_icon(icon):
    if IS_28:
        icon_28 = ICONS_279_TO_280.get(icon, None)
        if icon_28:
            return icon_28
    return icon


def layout_split(layout, percentage, align=False):
    if IS_28:
        split = layout.split(factor=percentage, align=align)
    else:
        split = layout.split(percentage=percentage, align=align)
    return split


def assign_props(items, replace=True):
    if IS_28:
        for item in items:
            props, clas = item
            if replace:
                clas.__annotations__ = props
            else:
                clas.__annotations__.update(props)
    else:
        for item in items:
            props, clas = item
            for prop_name, prop_value in props.items():
                setattr(clas, prop_name, prop_value)


IMAGE_NODES = ('TEX_IMAGE', 'TEX_ENVIRONMENT')


def is_all_empty_textures(material):
    if IS_28:
        return all(not node.type in IMAGE_NODES for node in material.node_tree.nodes)
    else:
        return all(not slot for slot in material.texture_slots)


def link_object(obj):
    if IS_28:
        bpy.context.scene.collection.objects.link(obj)
    else:
        bpy.context.scene.objects.link(obj)


def set_active_object(obj):
    if IS_28:
        bpy.context.view_layer.objects.active = obj
    else:
        bpy.context.scene.objects.active = obj


def select_object(obj):
    if IS_28:
        obj.select_set(True)
    else:
        obj.select = True


@contextlib.contextmanager
def using_active_object(obj):
    objects = bpy.context.view_layer.objects if IS_28 else bpy.context.scene.objects
    original = objects.active
    objects.active = obj
    try:
        yield
    finally:
        objects.active = original


def multiply(*elements):
    result = elements[0]
    if IS_28:
        for element in elements[1 : ]:
            result = result @ element
    else:
        for element in elements[1 : ]:
            result *= element
    return result


def multiply_27x(*elements):
    result = elements[0]
    for element in elements[1 : ]:
        result *= element
    return result


def multiply_28x(*elements):
    result = elements[0]
    for element in elements[1 : ]:
        result = result @ element
    return result


def get_multiply():
    if IS_28:
        return multiply_28x
    else:
        return multiply_27x


def get_prop_name(prop):
    if IS_293:
        name = prop.keywords.get('name', '')
    else:
        name = prop[1].get('name', '')
    return name


def get_preferences():
    if IS_28:
        return bpy.context.preferences.addons['io_scene_xray'].preferences
    else:
        return bpy.context.user_preferences.addons['io_scene_xray'].preferences


def set_arm_display_type(arm, display_type='STICK'):
    if IS_28:
        arm.display_type = display_type
    else:
        arm.draw_type = display_type
