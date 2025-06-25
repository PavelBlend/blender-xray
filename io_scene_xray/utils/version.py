# standart modules
import contextlib

# blender modules
import bpy
import bmesh

# addon modules
from .. import log
from .. import text


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


def is_blender_33():
    return bpy.app.version >= (3, 3, 0)


def is_blender_34():
    return bpy.app.version >= (3, 4, 0)


def is_blender_4():
    return bpy.app.version >= (4, 0, 0)


def is_blender_41():
    return bpy.app.version >= (4, 1, 0)


def is_blender_44():
    return bpy.app.version >= (4, 4, 0)


def support_principled_shader():
    return bpy.app.version >= (2, 79, 0)


def support_vertex_color_node():
    return bpy.app.version >= (2, 81, 0)


def support_shadow_method():
    return (2, 80, 0) <= bpy.app.version < (4, 3, 0)


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
IS_33 = is_blender_33()
IS_34 = is_blender_34()
IS_4 = is_blender_4()
IS_41 = is_blender_41()
IS_44 = is_blender_44()


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
    'FONT_DATA': 'FAKE_USER_ON',
    'MANIPUL': 'LIGHTPROBE_GRID',
    'MESH_ICOSPHERE': 'NORMALS_FACE',
    'MOD_EDGESPLIT': 'NORMALS_VERTEX_FACE'
}
ICONS_40_TO_41 = {
    'MANIPUL': 'LIGHTPROBE_VOLUME',
}

if IS_41:
    ICONS_279_TO_280.update(ICONS_40_TO_41)

SHADER_NODES = {
    'ShaderNodeMix': 'ShaderNodeMixRGB',
    'Factor': 'Fac'
}

if IS_4:
    SPECULAR = 'Specular IOR Level'
    BONE_GROUPS = 'collections'
else:
    SPECULAR = 'Specular'
    BONE_GROUPS = 'bone_groups'

CYCLES_COMPATIBLE_RENDS = (
    'CYCLES',
    'BLENDER_EEVEE',
    'BLENDER_EEVEE_NEXT',
    'BLENDER_WORKBENCH'
)
INTERAL_COMPATIBLE_RENDS = ('BLENDER_RENDER', 'BLENDER_GAME')


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


def remove_object(obj):
    if IS_277:
        bpy.context.scene.objects.unlink(obj)
        obj.user_clear()
        bpy.data.objects.remove(obj)
    
    else:
        bpy.data.objects.remove(obj, do_unlink=True)


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


def _set_geom_sel(mesh, sel, attr_name, domain):
    if IS_34:
        if attr_name in mesh.attributes:
            attr = mesh.attributes[attr_name]
        else:
            attr = mesh.attributes.new(attr_name, 'BOOLEAN', domain)
        attr.data.foreach_set('value', sel)

    else:
        if attr_name == '.select_vert':
            data = mesh.vertices
        elif attr_name == '.select_edge':
            data = mesh.edges
        else:
            data = mesh.polygons

        data.foreach_set('select', sel)


def set_vert_sel(mesh, sel):
    # set vertices selection
    _set_geom_sel(mesh, sel, '.select_vert', 'POINT')


def set_edge_sel(mesh, sel):
    # set edges selection
    _set_geom_sel(mesh, sel, '.select_edge', 'EDGE')


def set_face_sel(mesh, sel):
    # set faces selection
    _set_geom_sel(mesh, sel, '.select_poly', 'FACE')


def get_used_mats(bpy_mesh):
    mats = [None] * len(bpy_mesh.polygons)

    if IS_34:
        mat_attr = bpy_mesh.attributes.get('material_index')
        created_attr = False
        if not mat_attr:
            mat_attr = bpy_mesh.attributes.new(
                name='material_index',
                type='INT',
                domain='FACE'
            )
            created_attr = True
        mat_attr.data.foreach_get('value', mats)
        if created_attr:
            bpy_mesh.attributes.remove(mat_attr)

    else:
        bpy_mesh.polygons.foreach_get('material_index', mats)

    mats = tuple(set(mats))
    return mats


def get_bone_groups(obj):
    if IS_4:
        return obj.data.collections
    else:
        return obj.pose.bone_groups


def get_bone_group(obj, bone):
    if IS_4:
        bone = obj.data.bones[bone.name]
        colls_count = len(bone.collections)
        if colls_count == 1:
            return bone.collections[0]
        elif not colls_count:
            return None
        else:
            raise log.AppError(
                text.error.bone_many_colls,
                log.props(object=obj.name, bone=bone.name)
            )
    else:
        bone = obj.pose.bones[bone.name]
        return bone.bone_group


def assign_bone_group(obj, bone_name, bgroup):
    if IS_4:
        bgroup.assign(obj.data.bones[bone_name])
    else:
        obj.pose.bones[bone_name].bone_group = bgroup


arm_layers = [False, ] * 32

first_layer = arm_layers.copy()
first_layer[0] = True

deform_layer = arm_layers.copy()
deform_layer[31] = True

ik_layer = arm_layers.copy()
ik_layer[30] = True

MAIN_COLL = 'Main'
DEFORM_COLL = 'Deform'
IK_COLL = 'IK'


def _set_bone_layer(arm, bone, layer_or_coll):
    if IS_4:
        colls = arm.collections
        coll = colls.get(layer_or_coll)
        if not coll:
            coll = colls.new(name=layer_or_coll)
        coll.assign(bone)
    else:
        bone.layers = layer_or_coll


def set_first_layer(arm, bone):
    if IS_4:
        layer_or_coll = MAIN_COLL
    else:
        layer_or_coll = first_layer
    _set_bone_layer(arm, bone, layer_or_coll)


def set_deform_layer(arm, bone):
    if IS_4:
        layer_or_coll = DEFORM_COLL
    else:
        layer_or_coll = deform_layer
    _set_bone_layer(arm, bone, layer_or_coll)


def set_ik_layer(arm, bone):
    if IS_4:
        layer_or_coll = IK_COLL
    else:
        layer_or_coll = ik_layer
    _set_bone_layer(arm, bone, layer_or_coll)


def remove_bone_colls(arm):
    if IS_4:
        colls = arm.collections
        for coll in colls:
            colls.remove(coll)


class GroupInterface:
    def __init__(self, group):
        self.group = group

    def _create_group_socket(self, typ, name, in_out):
        if IS_4:
            socket = self.group.interface.new_socket(
                name=name,
                socket_type=typ,
                in_out=in_out
            )
        else:
            if in_out == 'INPUT':
                socket = self.group.inputs.new(typ, name)
            else:
                socket = self.group.outputs.new(typ, name)
        return socket

    def create_group_input(self, typ, name):
        return self._create_group_socket(typ, name, 'INPUT')

    def create_group_output(self, typ, name):
        return self._create_group_socket(typ, name, 'OUTPUT')


def run_op_ctx(operator, override_context, *args, **kwargs):
    # execute operator with context override
    if IS_4:
        with bpy.context.temp_override(**override_context):
            operator(*args, **kwargs)
    else:
        operator(override_context, *args, **kwargs)


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
