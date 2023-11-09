# blender modules
import bpy

# addon modules
from .. import utils


def _get_visuals_meshes(parent_obj, meshes, children):
    for child_obj in children[parent_obj]:
        if child_obj.xray.level.object_type == 'VISUAL':

            if child_obj.xray.level.visual_type == 'HIERRARHY':
                _get_visuals_meshes(child_obj, meshes, children)

            else:
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

    # get diffuse image from node tree
    if not diffuse_img:
        active_node = mat.node_tree.nodes.active
        active_img = None
        all_img_nodes = set()

        for node in mat.node_tree.nodes:
            if node.bl_idname == 'ShaderNodeTexImage':
                img = node.image
                if img:
                    all_img_nodes.add(node)
                    if active_node == node:
                        active_img = img

        if active_img:
            diffuse_img = active_img

        else:
            selected_imgs = []

            for img_node in all_img_nodes:
                if img_node.select:
                    selected_imgs.append(img_node.image)

            if len(selected_imgs) == 1:
                diffuse_img = selected_imgs[0]

    return diffuse_img


def _create_shader_nodes(mat, shader_groups):
    use_lmap_1 = False
    use_lmap_2 = False
    use_hemi = False
    use_light = False
    use_sun = False

    # get diffuse image
    diff_img = _get_diffuse_img(mat)
    if not diff_img:
        return

    # remove all nodes
    mat.node_tree.nodes.clear()

    # create image node
    img_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    img_node.image = diff_img
    img_node.select = False
    img_node.location.x = -200
    img_node.location.y = 500

    xray = mat.xray

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

    # create light maps
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

    # create group node
    group = mat.node_tree.nodes.new('ShaderNodeGroup')
    group.select = False
    group.width = 350
    group.location.x = img_node.location.x + 500
    group.location.y = img_node.location.y - 300

    shader_group = shader_groups.get((
        use_lmap_1,
        use_lmap_2,
        use_hemi,
        use_light,
        use_sun
    ))
    if not shader_group:
        shader_group = bpy.data.node_groups.new(
            'Level Shader Group',
            'ShaderNodeTree'
        )
        shader_groups[(
            use_lmap_1,
            use_lmap_2,
            use_hemi,
            use_light,
            use_sun
        )] = shader_group

        shader_group.inputs.new('NodeSocketColor', 'Texture Color')
        shader_group.inputs.new('NodeSocketFloat', 'Texture Alpha')

        shader_group.inputs.new('NodeSocketColor', 'Light Map 1 Color')
        shader_group.inputs.new('NodeSocketFloat', 'Light Map 1 Alpha')

        shader_group.inputs.new('NodeSocketColor', 'Light Map 2 Color')
        shader_group.inputs.new('NodeSocketFloat', 'Light Map 2 Alpha')

        shader_group.inputs.new('NodeSocketColor', 'Light Color')
        shader_group.inputs.new('NodeSocketColor', 'Sun Color')
        shader_group.inputs.new('NodeSocketColor', 'Hemi Color')

        shader_group.outputs.new('NodeSocketShader', 'Shader')

        # create group nodes
        input_node = shader_group.nodes.new('NodeGroupInput')
        input_node.select = False
        input_node.location.x = -800

        output_node = shader_group.nodes.new('NodeGroupOutput')
        output_node.select = False
        output_node.location.x = 800

        princp_node = shader_group.nodes.new('ShaderNodeBsdfPrincipled')
        princp_node.select = False
        princp_node.location.x = 500

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

        shader_group.nodes.update()

        # link

        shader_group.links.new(
            princp_node.outputs['BSDF'],
            output_node.inputs['Shader']
        )

        shader_group.links.new(
            lmap.outputs[2],    # Result
            princp_node.inputs['Base Color']
        )
        shader_group.links.new(
            input_node.outputs['Texture Alpha'],
            princp_node.inputs['Alpha']
        )

        shader_group.links.new(
            input_node.outputs['Light Map 1 Color'],
            light_sun.inputs[6]    # A
        )
        shader_group.links.new(
            input_node.outputs['Light Map 1 Alpha'],
            light_sun.inputs[7]    # B
        )

        shader_group.links.new(
            light_sun.outputs[2],    # Result
            hemi.inputs[6]    # A
        )
        shader_group.links.new(
            input_node.outputs['Light Map 2 Color'],
            hemi.inputs[7]    # B
        )

        shader_group.links.new(
            input_node.outputs['Texture Color'],
            lmap.inputs[6]    # A
        )
        shader_group.links.new(
            hemi.outputs[2],    # Result
            lmap.inputs[7]    # B
        )

    group.node_tree = shader_group

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


class XRAY_OT_create_level_shader_nodes(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.create_level_shader_nodes'
    bl_label = 'Create Level Shader Nodes'
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        default='ACTIVE_LEVEL',
        items=(
            ('ACTIVE_LEVEL', 'Active Level', ''),
            ('SELECTED_LEVELS', 'Selected Levels', ''),
            ('ALL_LEVELS', 'All Levels', ''),

            ('ACTIVE_OBJECT', 'Active Object', ''),
            ('SELECTED_OBJECTS', 'Selected Objects', ''),
            ('ALL_OBJECTS', 'All Objects', ''),

            ('ACTIVE_MATERIAL', 'Active Material', ''),
            ('ALL_MATERIALS', 'All Materials', '')
        )
    )

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)

        column.prop(self, 'mode', expand=True)

    def execute(self, context):
        import time
        st = time.time()

        materials = _get_materials(self.mode)

        change_count = 0
        shader_groups = {}

        for mat in materials:
            _create_shader_nodes(mat, shader_groups)
            change_count += 1

        et = time.time()
        print('{:.3f} sec'.format(et - st))

        self.report({'INFO'}, 'Changed materials: {}'.format(change_count))

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    utils.version.register_classes(XRAY_OT_create_level_shader_nodes)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_create_level_shader_nodes)
