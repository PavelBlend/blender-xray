# standart modules
import contextlib

# blender modules
import bpy
import bmesh


def is_blender_2_77():
    return bpy.app.version <= (2, 77, 0)


def is_blender_2_80():
    return bpy.app.version >= (2, 80, 0)


def is_blender_2_90():
    return bpy.app.version >= (2, 90, 0)


def is_blender_2_93():
    return bpy.app.version >= (2, 93, 0)


def is_blender_3():
    return bpy.app.version >= (3, 0, 0)


def is_blender_34():
    return bpy.app.version >= (3, 4, 0)


def support_principled_shader():
    return bpy.app.version >= (2, 79, 0)


def support_vertex_color_node():
    return bpy.app.version >= (2, 81, 0)


def has_set_normals_from_faces():
    return bpy.app.version >= (2, 79, 0)


def broken_file_browser_filter():
    return bpy.app.version >= (2, 90, 0)


def broken_uv_layers():
    return bpy.app.version >= (3, 5, 0)


def has_file_browser_show_tool_prop():
    return bpy.app.version >= (3, 0, 0)


def has_asset_browser():
    return bpy.app.version >= (3, 0, 0)


def has_id_props_ui():
    return bpy.app.version >= (3, 0, 0)


IS_277 = is_blender_2_77()
IS_28 = is_blender_2_80()
IS_29 = is_blender_2_90()
IS_293 = is_blender_2_93()
IS_3 = is_blender_3()
IS_34 = is_blender_34()


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
    'BUTS': 'PROPERTIES',
    'FONT_DATA': 'FAKE_USER_ON'
}

SHADER_NODES = {
    'ShaderNodeMix': 'ShaderNodeMixRGB',
    'Factor': 'Fac'
}


def get_icon(icon):
    if IS_28:
        icon_28 = ICONS_279_TO_280.get(icon, None)
        if icon_28:
            return icon_28
    return icon


def get_node(node, ver):
    if not ver:
        node = SHADER_NODES.get(node, None)
    return node


def get_action_panel_space():
    if bpy.app.version >= (2, 78, 0):
        return 'DOPESHEET_EDITOR'
    else:
        return 'GRAPH_EDITOR'


def layout_split(layout, percentage, align=False):
    if IS_28:
        split = layout.split(factor=percentage, align=align)
    else:
        split = layout.split(percentage=percentage, align=align)
    return split


def _make_annotations(cls):
    """Converts class fields to annotations if running with Blender 2.8"""
    if bpy.app.version < (2, 80):
        return cls

    if bpy.app.version >= (2, 93):
        bl_props = {
            key: value
            for key, value in cls.__dict__.items()
                if isinstance(value, bpy.props._PropertyDeferred)
        }

    else:
        bl_props = {
            key: value
            for key, value in cls.__dict__.items()
                if isinstance(value, tuple)
        }

    if bl_props:

        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})

        annotations = cls.__dict__['__annotations__']

        for key, value in bl_props.items():
            annotations[key] = value
            delattr(cls, key)

    return cls


def _register_class(clas):
    _make_annotations(clas)
    bpy.utils.register_class(clas)

    b_type = getattr(clas, 'b_type', None)
    if b_type:
        b_type.xray = bpy.props.PointerProperty(type=clas)


def register_classes(operators):
    if hasattr(operators, '__iter__'):
        for operator in operators:
            _register_class(operator)
    else:
        _register_class(operators)


def _unregister_prop_group(clas):
    # clas inherits from bpy.types.PropertyGroup
    if hasattr(clas, 'b_type'):
        del clas.b_type.xray

    bpy.utils.unregister_class(clas)


def unregister_prop_groups(classes):
    if hasattr(classes, '__iter__'):
        # clas inherits from bpy.types.PropertyGroup
        for clas in reversed(classes):
            _unregister_prop_group(clas)
    else:
        _unregister_prop_group(classes)


IMAGE_NODES = ('TEX_IMAGE', 'TEX_ENVIRONMENT')


def is_all_empty_textures(material):
    if IS_28:
        return all(
            not node.type in IMAGE_NODES
            for node in material.node_tree.nodes
        )
    else:
        return all(not slot for slot in material.texture_slots)


def link_object(obj):
    if IS_28:
        bpy.context.scene.collection.objects.link(obj)
    else:
        if not bpy.context.scene.objects.get(obj.name):
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


def set_mesh_objects_select(objs_names, select_state):
    if IS_28:
        for obj_name in objs_names:
            obj = bpy.data.objects[obj_name]
            if obj.type == 'MESH':
                obj.select_set(select_state)
    else:
        for obj_name in objs_names:
            obj = bpy.data.objects[obj_name]
            if obj.type == 'MESH':
                obj.select = select_state


def set_object_select(obj, select_state):
    if IS_28:
        obj.select_set(select_state)
    else:
        obj.select = select_state


def get_object_visibility(obj):
    if IS_28:
        return obj.visible_get()
    else:
        return obj.is_visible(bpy.context.scene)


@contextlib.contextmanager
def using_active_object(obj):
    if IS_28:
        objects = bpy.context.view_layer.objects
    else:
        objects = bpy.context.scene.objects
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


def create_bmesh_cone(
        mesh,
        segments=32,
        radius_1=1.0,
        radius_2=1.0,
        depth=2.0
    ):
    if IS_3:
        bmesh.ops.create_cone(
            mesh,
            segments=segments,
            radius1=radius_1,
            radius2=radius_1,
            depth=depth
        )
    else:
        bmesh.ops.create_cone(
            mesh,
            segments=segments,
            diameter1=radius_1,
            diameter2=radius_1,
            depth=depth
        )


def create_bmesh_icosphere(
        mesh,
        subdivisions=2,
        radius=1.0
    ):
    if IS_3:
        bmesh.ops.create_icosphere(
            mesh,
            subdivisions=subdivisions,
            radius=radius
        )
    else:
        bmesh.ops.create_icosphere(
            mesh,
            subdivisions=subdivisions,
            diameter=radius
        )


def set_object_draw_type(bpy_object, draw_type):
    if IS_28:
        bpy_object.display_type = draw_type
    else:
        bpy_object.draw_type = draw_type


def set_object_show_xray(bpy_object, show_xray):
    if IS_28:
        bpy_object.show_in_front = show_xray
    else:
        bpy_object.show_x_ray = show_xray


def set_empty_draw_type(empty_object, draw_type):
    if IS_28:
        empty_object.empty_display_type = draw_type
    else:
        empty_object.empty_draw_type = draw_type


def set_empty_draw_size(empty_object, draw_size):
    if IS_28:
        empty_object.empty_display_size = draw_size
    else:
        empty_object.empty_draw_size = draw_size


def remove_action(action):
    action.user_clear()
    if not IS_277:
        bpy.data.actions.remove(action, do_unlink=True)
    else:
        bpy.data.actions.remove(action)


def create_collection(collection_name, parent_collection=None):
    if IS_28:
        collection = bpy.data.collections.new(collection_name)
        if not parent_collection:
            parent_collection = bpy.context.scene.collection
        parent_collection.children.link(collection)
    else:
        collection = bpy.data.groups.new(collection_name)
    return collection


def remove_collection(collection):
    if IS_28:
        bpy.data.collections.remove(collection)
    else:
        if IS_277:
            bpy.data.groups.remove(collection)
        else:
            bpy.data.groups.remove(collection, do_unlink=True)


def unlink_object_from_collections(obj):
    if IS_28:
        for child in obj.children:
            unlink_object_from_collections(child)
        for collection in obj.users_collection:
            collection.objects.unlink(obj)


def link_object_to_collection(obj, collection):
    for child in obj.children:
        link_object_to_collection(child, collection)
    collection.objects.link(obj)


@contextlib.contextmanager
def using_mode(mode):
    if IS_28:
        objects = bpy.context.view_layer.objects
    else:
        objects = bpy.context.scene.objects
    original = objects.active.mode
    bpy.ops.object.mode_set(mode=mode)
    try:
        yield
    finally:
        bpy.ops.object.mode_set(mode=original)
