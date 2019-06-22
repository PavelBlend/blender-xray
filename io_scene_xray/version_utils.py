import bpy


def is_blender_2_80():
    return bpy.app.version >= (2, 80, 0)


IS_28 = is_blender_2_80()


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
    'BBOX': 'SHADING_BBOX'
}


def get_icon(icon):
    if IS_28:
        icon_28 = ICONS_279_TO_280.get(icon, None)
        if icon_28:
            return icon_28
    return icon


def layout_split(layout, percentage):
    if IS_28:
        split = layout.split(factor=percentage)
    else:
        split = layout.split(percentage=percentage)
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


def is_all_empty_textures(material):
    if IS_28:
        return all(node.type != 'TEX_IMAGE' for node in material.node_tree.nodes)
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


def multiply(*elements):
    result = elements[0]
    if IS_28:
        for element in elements[1 : ]:
            result = result @ element
    else:
        for element in elements[1 : ]:
            result *= element
    return result