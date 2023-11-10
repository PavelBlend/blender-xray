# blender modules
import bpy
import mathutils

# addon modules
from .. import utils


def _get_visuals_meshes(parent_obj, meshes, children):
    child_objs = children.get(parent_obj)

    if not child_objs:
        return

    for child_obj in child_objs:
        if child_obj.xray.level.object_type == 'VISUAL':

            if child_obj.xray.level.visual_type in ('HIERRARHY', 'LOD'):
                _get_visuals_meshes(child_obj, meshes, children)

            else:
                if child_obj.type == 'MESH':
                    meshes.add(child_obj.data)


def _get_level_meshes(level_obj, meshes, children):
    # get sectors object
    sectors_obj = None
    sectors_obj_name = level_obj.xray.level.sectors_obj

    if sectors_obj_name:
        sectors_obj = bpy.data.objects.get(sectors_obj_name)

    if not sectors_obj:
        for level_child in children[level_obj]:

            if level_child.name.startswith('sectors'):
                sectors_obj = level_child
                break

    # collect meshes
    if sectors_obj:
        for sector_obj in children[sectors_obj]:
            _get_visuals_meshes(sector_obj, meshes, children)


def _get_children(mode):
    children = {}

    if mode in ('ACTIVE_LEVEL', 'SELECTED_LEVELS', 'ALL_LEVELS'):
        for obj in bpy.data.objects:

            if obj.parent:
                children.setdefault(obj.parent, []).append(obj)

    return children


def _get_materials(mode):
    mats = set()
    meshes = set()
    children = _get_children(mode)

    # active level
    if mode == 'ACTIVE_LEVEL':
        obj = bpy.context.active_object
        if obj:
            if obj.xray.level.object_type == 'LEVEL':
                _get_level_meshes(obj, meshes, children)

    # selected levels
    elif mode == 'SELECTED_LEVELS':
        for obj in bpy.context.selected_objects:
            if obj.xray.level.object_type == 'LEVEL':
                _get_level_meshes(obj, meshes, children)

    # all levels
    elif mode == 'ALL_LEVELS':
        for obj in bpy.data.objects:
            if obj.xray.level.object_type == 'LEVEL':
                _get_level_meshes(obj, meshes, children)

    # active object
    elif mode == 'ACTIVE_OBJECT':
        obj = bpy.context.active_object
        if obj:
            if obj.type == 'MESH':
                meshes.add(obj.data)

    # selected objects
    elif mode == 'SELECTED_OBJECTS':
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                meshes.add(obj.data)

    # all objects
    elif mode == 'ALL_OBJECTS':
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                meshes.add(obj.data)

    # active material
    elif mode == 'ACTIVE_MATERIAL':
        obj = bpy.context.active_object
        if obj:
            if obj.type == 'MESH':
                mat = obj.active_material
                if mat:
                    mats.add(mat)

    # all materials
    elif mode == 'ALL_MATERIALS':
        for mat in bpy.data.materials:
            mats.add(mat)

    if meshes:
        for mesh in meshes:
            for mat in mesh.materials:
                if mat:
                    mats.add(mat)

    return mats


def _get_diffuse_img(mat):
    # get output node
    output_node = None

    if mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.bl_idname == 'ShaderNodeOutputMaterial':
                if node.is_active_output:
                    output_node = node
                    break

    # get diffuse image from output node
    diffuse_img = None

    if output_node:
        surface_input = output_node.inputs['Surface']

        if surface_input.links:
            surface = surface_input.links[0].from_node

            # get image from image node
            if surface.bl_idname == 'ShaderNodeTexImage':
                img = surface.image
                if img:
                    diffuse_img = img

            # get image from shader node
            if not diffuse_img:
                color_input = surface.inputs.get('Color')

                if not color_input:
                    color_input = surface.inputs.get('Base Color')

                if color_input:
                    if color_input.links:
                        color = color_input.links[0].from_node
                        if color.bl_idname == 'ShaderNodeTexImage':
                            img = color.image
                            if img:
                                diffuse_img = img

    # get light map images
    lmap_imgs = set()
    for lmap in (mat.xray.lmap_0, mat.xray.lmap_1):
        if lmap:
            lmap_img = bpy.data.images.get(lmap)
            if lmap_img:
                lmap_imgs.add(lmap_img)

    # get diffuse image from node tree
    if not diffuse_img:
        active_img = None
        all_img_nodes = set()

        if mat.node_tree:
            for node in mat.node_tree.nodes:
                if node.bl_idname == 'ShaderNodeTexImage':
                    img = node.image
                    if img:
                        if img in lmap_imgs:
                            continue
                        all_img_nodes.add(node)
                        if node == mat.node_tree.nodes.active:
                            active_img = img

        if active_img:
            diffuse_img = active_img

        elif len(all_img_nodes) == 1:
            diffuse_img = list(all_img_nodes)[0].image

        else:
            selected_imgs = []

            for img_node in all_img_nodes:
                if img_node.select:
                    selected_imgs.append(img_node.image)

            if len(selected_imgs) == 1:
                diffuse_img = selected_imgs[0]

    return diffuse_img


def _create_diffuse_image_nodes(mat, diff_img, xray):
    # create image node
    img_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    img_node.image = diff_img
    img_node.select = False
    img_node.location.x = -200
    img_node.location.y = 500

    # create diffuse uv-map node
    if xray.uv_texture:
        uv_tex_node = mat.node_tree.nodes.new('ShaderNodeUVMap')
        uv_tex_node.uv_map = xray.uv_texture
        uv_tex_node.select = False
        uv_tex_node.location.x = img_node.location.x - 250
        uv_tex_node.location.y = img_node.location.y - 100

        # link
        mat.node_tree.links.new(
            uv_tex_node.outputs['UV'],
            img_node.inputs['Vector']
        )

    return img_node


def _create_lmap_image_nodes(mat, xray, img_node):
    use_lmap_1 = False
    use_lmap_2 = False
    lmap_imgs = []

    if xray.lmap_0 or xray.lmap_1:

        # create light map uv node
        uv_lmap_node = mat.node_tree.nodes.new('ShaderNodeUVMap')
        uv_lmap_node.uv_map = xray.uv_light_map
        uv_lmap_node.select = False

        # create light map image nodes
        for i, lmap in enumerate((xray.lmap_0, xray.lmap_1)):
            if lmap:
                lmap_img = bpy.data.images.get(lmap)
                if lmap_img:
                    lmap_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
                    lmap_node.image = lmap_img
                    lmap_node.select = False
                    lmap_node.location.x = img_node.location.x
                    lmap_node.location.y = img_node.location.y - (i+1) * 300
                    lmap_imgs.append(lmap_node)

                    # link
                    mat.node_tree.links.new(
                        uv_lmap_node.outputs['UV'],
                        lmap_node.inputs['Vector']
                    )

        # move uv-map node
        if len(lmap_imgs) == 1:
            use_lmap_1 = True
            loc = lmap_imgs[0].location
            uv_lmap_node.location.x = loc.x - 250
            uv_lmap_node.location.y = loc.y - 100

        elif len(lmap_imgs) == 2:
            use_lmap_1 = True
            use_lmap_2 = True
            loc_1 = lmap_imgs[0].location
            loc_2 = lmap_imgs[1].location
            uv_lmap_node.location.x = loc_1.x - 250
            uv_lmap_node.location.y = (loc_1.y + loc_2.y) / 2 - 100

    return lmap_imgs, use_lmap_1, use_lmap_2


def _create_vert_color_node(shader_group, col_name, name, loc):
    if col_name:

        col_node = shader_group.nodes.new('ShaderNodeVertexColor')
        col_node.name = name
        col_node.layer_name = col_name
        col_node.select = False
        col_node.location = loc

        return col_node


def _create_vert_col_nodes(mat, shader_group):
    xray = mat.xray

    light_node = _create_vert_color_node(
        shader_group,
        xray.light_vert_color,
        'Light',
        mathutils.Vector((-800, 300))
    )
    sun_node = _create_vert_color_node(
        shader_group,
        xray.sun_vert_color,
        'Sun',
        mathutils.Vector((-800, 150))
    )
    hemi_node = _create_vert_color_node(
        shader_group,
        xray.hemi_vert_color,
        'Hemi',
        mathutils.Vector((-400, -200))
    )

    return light_node, sun_node, hemi_node


def _create_group_nodes(mat, img_node, shader_groups, use_lmap_1, use_lmap_2):
    # create group node
    group = mat.node_tree.nodes.new('ShaderNodeGroup')
    group.select = False
    group.width = 350
    group.location.x = img_node.location.x + 500
    group.location.y = img_node.location.y - 300

    use_light = bool(mat.xray.light_vert_color)
    use_sun = bool(mat.xray.sun_vert_color)
    use_hemi = bool(mat.xray.hemi_vert_color)

    usage = (use_lmap_1, use_lmap_2, use_light, use_sun, use_hemi)

    shader_group = shader_groups.get(usage)

    if not shader_group:
        if use_lmap_1 and use_lmap_2:
            group_suffix = 'Light Map'

        elif use_lmap_1 and not use_lmap_2:
            group_suffix = 'Terrain'

        elif use_light and use_sun and use_hemi:
            group_suffix = 'Vertex Color'

        elif use_hemi and not use_light and not use_sun:
            group_suffix = 'Multiple Usage'

        else:
            group_suffix = ''

        if group_suffix:
            group_suffix = ': ' + group_suffix

        shader_group = bpy.data.node_groups.new(
            'Level Shader Group{}'.format(group_suffix),
            'ShaderNodeTree'
        )
        shader_groups[usage] = shader_group

        # create inputs
        tex_rgb = shader_group.inputs.new('NodeSocketColor', 'Texture Color')
        tex_rgb.hide_value = True
        tex_a = shader_group.inputs.new('NodeSocketFloat', 'Texture Alpha')
        tex_a.hide_value = True

        lmap_rgb = shader_group.inputs.new('NodeSocketColor', 'Light Map 1 Color')
        lmap_rgb.hide_value = True
        lmap_a = shader_group.inputs.new('NodeSocketFloat', 'Light Map 1 Alpha')
        lmap_a.hide_value = True

        lmap_rgb = shader_group.inputs.new('NodeSocketColor', 'Light Map 2 Color')
        lmap_rgb.hide_value = True
        lmap_a = shader_group.inputs.new('NodeSocketFloat', 'Light Map 2 Alpha')
        lmap_a.hide_value = True

        # create outputs
        shader_group.outputs.new('NodeSocketShader', 'Shader')

        # create group nodes
        input_node = shader_group.nodes.new('NodeGroupInput')
        input_node.select = False
        input_node.location.x = -800

        output_node = shader_group.nodes.new('NodeGroupOutput')
        output_node.select = False
        output_node.location.x = 800

        # create shader node
        princp_node = shader_group.nodes.new('ShaderNodeBsdfPrincipled')
        princp_node.select = False
        princp_node.location.x = 500
        princp_node.inputs['Specular'].default_value = 0.0

        # link shader
        shader_group.links.new(
            princp_node.outputs['BSDF'],
            output_node.inputs['Shader']
        )
        alpha_link = shader_group.links.new(
            input_node.outputs['Texture Alpha'],
            princp_node.inputs['Alpha']
        )

        # create color mix nodes
        light_sun = shader_group.nodes.new('ShaderNodeMix')
        light_sun.name = 'Light + Sun'
        light_sun.label = 'Light + Sun'
        light_sun.blend_type = 'ADD'
        light_sun.data_type = 'RGBA'
        light_sun.inputs['Factor'].default_value = 1.0
        light_sun.select = False
        light_sun.location.x = -500
        light_sun.location.y = 200

        hemi = shader_group.nodes.new('ShaderNodeMix')
        hemi.name = '+ Hemi'
        hemi.label = '+ Hemi'
        hemi.blend_type = 'ADD'
        hemi.data_type = 'RGBA'
        hemi.inputs['Factor'].default_value = 1.0
        hemi.select = False
        hemi.location.x = -150
        hemi.location.y = 0

        lmap = shader_group.nodes.new('ShaderNodeMix')
        lmap.name = 'Diffuse * Light Map'
        lmap.label = 'Diffuse * Light Map'
        lmap.blend_type = 'MULTIPLY'
        lmap.data_type = 'RGBA'
        lmap.inputs['Factor'].default_value = 1.0
        lmap.select = False
        lmap.location.x = 200
        lmap.location.y = 200

        # vertex colors
        light_node, sun_node, hemi_node = _create_vert_col_nodes(mat, shader_group)

        # link nodes

        shader_group.links.new(
            lmap.outputs[2],    # Result
            princp_node.inputs['Base Color']
        )
        shader_group.links.new(
            input_node.outputs['Texture Color'],
            lmap.inputs[6]    # color A
        )
        shader_group.links.new(
            light_sun.outputs[2],    # Result
            hemi.inputs[6]    # color A
        )
        hemi_lmap = shader_group.links.new(
            hemi.outputs[2],    # Result
            lmap.inputs[7]    # color B
        )

        # link light maps
        if use_lmap_1 and use_lmap_2:
            shader_group.nodes.remove(hemi_node)

            shader_group.links.new(
                input_node.outputs['Light Map 1 Color'],
                light_sun.inputs[6]    # color A
            )
            shader_group.links.new(
                input_node.outputs['Light Map 1 Alpha'],
                light_sun.inputs[7]    # color B
            )
            shader_group.links.new(
                input_node.outputs['Light Map 2 Color'],
                hemi.inputs[7]    # color B
            )

        # link terrain
        elif use_lmap_1 and not use_lmap_2:
            shader_group.links.remove(alpha_link)
            shader_group.nodes.remove(hemi_node)

            shader_group.links.new(
                input_node.outputs['Texture Alpha'],
                hemi.inputs[7]    # color B
            )
            shader_group.links.new(
                input_node.outputs['Light Map 1 Color'],
                light_sun.inputs[6]    # color A
            )
            shader_group.links.new(
                input_node.outputs['Light Map 1 Alpha'],
                light_sun.inputs[7]    # color B
            )

        # link vertex colors
        elif light_node and sun_node and hemi_node:
            shader_group.links.new(
                light_node.outputs['Color'],
                light_sun.inputs[6]    # color A
            )
            shader_group.links.new(
                sun_node.outputs['Color'],
                light_sun.inputs[7]    # color B
            )
            shader_group.links.new(
                hemi_node.outputs['Color'],
                hemi.inputs[7]    # color B
            )

        # link multiple usage
        elif use_hemi and not use_light and not use_sun:
            shader_group.links.remove(hemi_lmap)
            shader_group.nodes.remove(light_sun)
            shader_group.nodes.remove(hemi)
            lmap.inputs['Factor'].default_value = 0.5

            shader_group.links.new(
                hemi_node.outputs['Color'],
                lmap.inputs[7]    # color B
            )

    group.node_tree = shader_group

    return group


def _create_and_link_nodes(mat, diff_img, shader_groups):
    xray = mat.xray

    # diffuse image
    img_node = _create_diffuse_image_nodes(mat, diff_img, xray)

    # light maps image
    lmap_imgs, use_lmap_1, use_lmap_2 = _create_lmap_image_nodes(
        mat,
        xray,
        img_node
    )

    # group node
    group = _create_group_nodes(
        mat,
        img_node,
        shader_groups,
        use_lmap_1,
        use_lmap_2
    )

    # create output node
    out_node = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    out_node.select = False
    out_node.location.x = group.location.x + 500
    out_node.location.y = group.location.y

    # link group

    mat.node_tree.links.new(
        group.outputs['Shader'],
        out_node.inputs['Surface']
    )

    # link diffuse image
    mat.node_tree.links.new(
        img_node.outputs['Color'],
        group.inputs['Texture Color']
    )

    mat.node_tree.links.new(
        img_node.outputs['Alpha'],
        group.inputs['Texture Alpha']
    )

    # link light map images
    if len(lmap_imgs) >= 1:
        mat.node_tree.links.new(
            lmap_imgs[0].outputs['Color'],
            group.inputs['Light Map 1 Color']
        )

        mat.node_tree.links.new(
            lmap_imgs[0].outputs['Alpha'],
            group.inputs['Light Map 1 Alpha']
        )

    if len(lmap_imgs) == 2:
        mat.node_tree.links.new(
            lmap_imgs[1].outputs['Color'],
            group.inputs['Light Map 2 Color']
        )

        mat.node_tree.links.new(
            lmap_imgs[1].outputs['Alpha'],
            group.inputs['Light Map 2 Alpha']
        )


def _create_shader_nodes(mat, shader_groups):
    # get diffuse image
    diff_img = _get_diffuse_img(mat)
    if not diff_img:
        return

    # remove all nodes
    mat.node_tree.nodes.clear()

    # create nodes
    _create_and_link_nodes(mat, diff_img, shader_groups)


def _create_base_nodes(mat, img):
    xray = mat.xray

    # create output node
    out_node = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    out_node.select = False
    out_node.location.x = 300
    out_node.location.y = 300

    # create shader node
    princp_node = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    princp_node.select = False
    princp_node.location.x = 10
    princp_node.location.y = 300
    princp_node.inputs['Specular'].default_value = 0.0

    # create image node
    img_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    img_node.image = img
    img_node.select = False
    img_node.location.x = -500
    img_node.location.y = 100

    # create uv-map node
    uv_name = xray.uv_texture
    if uv_name:
        uv_node = mat.node_tree.nodes.new('ShaderNodeUVMap')
        uv_node.uv_map = uv_name
        uv_node.select = False
        uv_node.location.x = -800
        uv_node.location.y = 100

        # link
        mat.node_tree.links.new(
            uv_node.outputs['UV'],
            img_node.inputs['Vector']
        )

    # link nodes
    mat.node_tree.links.new(
        princp_node.outputs['BSDF'],
        out_node.inputs['Surface']
    )
    mat.node_tree.links.new(
        img_node.outputs['Color'],
        princp_node.inputs['Base Color']
    )

    if not (xray.lmap_0 and not xray.lmap_1):    # is not terrain
        mat.node_tree.links.new(
            img_node.outputs['Alpha'],
            princp_node.inputs['Alpha']
        )


def _remove_shader_nodes(mat):
    # get diffuse image
    diff_img = _get_diffuse_img(mat)
    if not diff_img:
        return

    # remove all nodes
    mat.node_tree.nodes.clear()

    # create nodes
    _create_base_nodes(mat, diff_img)


mode_items = (
    ('ACTIVE_LEVEL', 'Active Level', ''),
    ('SELECTED_LEVELS', 'Selected Levels', ''),
    ('ALL_LEVELS', 'All Levels', ''),

    ('ACTIVE_OBJECT', 'Active Object', ''),
    ('SELECTED_OBJECTS', 'Selected Objects', ''),
    ('ALL_OBJECTS', 'All Objects', ''),

    ('ACTIVE_MATERIAL', 'Active Material', ''),
    ('ALL_MATERIALS', 'All Materials', '')
)


class _BaseOperator(utils.ie.BaseOperator):
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)

        column.prop(self, 'mode', expand=True)

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_create_level_shader_nodes(_BaseOperator):
    bl_idname = 'io_scene_xray.create_level_shader_nodes'
    bl_label = 'Create Level Shader Nodes'

    mode = bpy.props.EnumProperty(default='ACTIVE_LEVEL', items=mode_items)

    def execute(self, context):
        materials = _get_materials(self.mode)

        change_count = 0
        shader_groups = {}

        for mat in materials:
            _create_shader_nodes(mat, shader_groups)
            change_count += 1

        self.report({'INFO'}, 'Changed materials: {}'.format(change_count))

        return {'FINISHED'}


class XRAY_OT_remove_level_shader_nodes(_BaseOperator):
    bl_idname = 'io_scene_xray.remove_level_shader_nodes'
    bl_label = 'Remove Level Shader Nodes'

    mode = bpy.props.EnumProperty(default='ACTIVE_LEVEL', items=mode_items)

    def execute(self, context):
        materials = _get_materials(self.mode)

        change_count = 0

        for mat in materials:
            _remove_shader_nodes(mat)
            change_count += 1

        self.report({'INFO'}, 'Changed materials: {}'.format(change_count))

        return {'FINISHED'}


classes = (
    XRAY_OT_create_level_shader_nodes,
    XRAY_OT_remove_level_shader_nodes
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
