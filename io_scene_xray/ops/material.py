# standart modules
import os
import zlib

# blender modules
import bpy
import mathutils

# addon modules
from .. import formats
from .. import utils
from .. import text


def get_object_materials(bpy_object, materials):
    for material_slot in bpy_object.material_slots:
        material = material_slot.material
        if material:
            materials.add(material)


def get_materials(context, mode):
    materials = set()

    # active material
    if mode == 'ACTIVE_MATERIAL':
        if not context.active_object:
            return materials
        if context.active_object.active_material:
            materials.add(context.active_object.active_material)
        else:
            return materials

    # active object
    elif mode == 'ACTIVE_OBJECT':
        if not context.active_object:
            return materials
        get_object_materials(context.active_object, materials)

    # selected objects
    elif mode == 'SELECTED_OBJECTS':
        for bpy_object in context.selected_objects:
            get_object_materials(bpy_object, materials)

    # all objects
    elif mode == 'ALL_OBJECTS':
        for bpy_object in bpy.data.objects:
            get_object_materials(bpy_object, materials)

    # all materials
    else:
        for material in bpy.data.materials:
            materials.add(material)

    return materials


def get_image_nodes(node, image_nodes):
    for node_input in node.inputs:
        from_node = None
        for link in node_input.links:
            from_node = link.from_node
            break
        if from_node:
            if from_node.type in utils.version.IMAGE_NODES:
                image_nodes.append(from_node)
            get_image_nodes(from_node, image_nodes)


mode_prop = bpy.props.EnumProperty(
    name='Mode',
    items=(
        ('ACTIVE_MATERIAL', 'Active Material', ''),
        ('ACTIVE_OBJECT', 'Active Object', ''),
        ('SELECTED_OBJECTS', 'Selected Objects', ''),
        ('ALL_OBJECTS', 'All Objects', ''),
        ('ALL_MATERIALS', 'All Materials', '')
    ),
    default='ACTIVE_MATERIAL'
)


class XRAY_OT_switch_render(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.switch_render'
    bl_label = 'Switch Render'
    bl_description = 'Switch Cycles/Internal Render'
    bl_options = {'REGISTER', 'UNDO'}

    mode = mode_prop

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    @utils.set_cursor_state
    def execute(self, context):
        scene = context.scene

        # set render engine
        if scene.render.engine == 'CYCLES':
            scene.render.engine = 'BLENDER_RENDER'

        elif scene.render.engine == 'BLENDER_RENDER':
            scene.render.engine = 'CYCLES'

        else:
            scene.render.engine = 'BLENDER_RENDER'

        # collect materials
        materials = get_materials(context, self.mode)

        # change use nodes
        if scene.render.engine == 'CYCLES':
            for material in materials:
                material.use_nodes = True

        else:
            for material in materials:
                material.use_nodes = False

        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Changed {} material(s)'.format(len(materials)))

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_convert_to_internal_material(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.convert_to_internal'
    bl_label = 'Convert to Internal'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    mode = mode_prop

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    @utils.set_cursor_state
    def execute(self, context):
        materials = get_materials(context, self.mode)

        for material in materials:
            if not material.use_nodes:
                self.report({'WARNING'}, 'Material "{}" does not use cycles nodes.'.format(material.name))
                continue
            node_tree = material.node_tree
            nodes = node_tree.nodes
            output_node = None
            for node in nodes:
                if node.type == 'OUTPUT_MATERIAL':
                    if node.is_active_output:
                        output_node = node
                        break
            if not output_node:
                self.report({'WARNING'}, 'Material "{}" has no output node.'.format(material.name))
                continue
            image_nodes = []
            get_image_nodes(output_node, image_nodes)
            images = []
            for image_node in image_nodes:
                images.append(image_node.image)
            if len(images) != 1:
                self.report({'WARNING'}, 'Material "{}" has to many image nodes'.format(material.name))
                continue
            image = images[0]
            uv_map = None
            if len(image_nodes[0].inputs['Vector'].links):
                from_node = image_nodes[0].inputs['Vector'].links[0].from_node
                if from_node.type == 'UVMAP':
                    uv_map = from_node.uv_map
            material.use_nodes = False
            texture_slot = None
            find_texture = False
            for index, texture_slot in enumerate(material.texture_slots):
                if not find_texture:
                    if texture_slot:
                        texture = texture_slot.texture
                        texture.type = 'IMAGE'
                        texture.image = image
                        texture.name = image.name
                        if uv_map:
                            texture_slot.uv_layer = uv_map
                        break
                else:
                    material.texture_slots[index] = None
            if not texture_slot:
                bpy_texture = bpy.data.textures.new(image.name, 'IMAGE')
                bpy_texture.type = 'IMAGE'
                bpy_texture.image = image
                texture_slot = material.texture_slots.add()
                texture_slot.texture = bpy_texture
                if uv_map:
                    texture_slot.uv_layer = uv_map

        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Changed {} material(s)'.format(len(materials)))
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


shader_keys = {
    'PRINCIPLED': ['ShaderNodeBsdfPrincipled', 'Base Color', 'BSDF'],
    'DIFFUSE': ['ShaderNodeBsdfDiffuse', 'Color', 'BSDF'],
    'EMISSION': ['ShaderNodeEmission', 'Color', 'Emission']
}

if utils.version.support_principled_shader():
    convert_materials_shader_type_items = (
        ('PRINCIPLED', 'Principled', ''),
        ('DIFFUSE', 'Diffuse', ''),
        ('EMISSION', 'Emission', '')
    )
    default_shader = 'PRINCIPLED'
else:
    convert_materials_shader_type_items = (
        ('DIFFUSE', 'Diffuse', ''),
        ('EMISSION', 'Emission', '')
    )
    default_shader = 'DIFFUSE'


class XRAY_OT_convert_to_cycles_material(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.convert_to_cycles'
    bl_label = 'Convert to Cycles'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    mode = mode_prop
    shader_type = bpy.props.EnumProperty(
        name='Shader',
        items=convert_materials_shader_type_items,
        default=default_shader
    )

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)
        column.label(text='Shader Type:')
        column.prop(self, 'shader_type', expand=True)

    @utils.set_cursor_state
    def execute(self, context):
        materials = get_materials(context, self.mode)

        for material in materials:
            material.use_nodes = True
            node_tree = material.node_tree
            nodes = node_tree.nodes
            for node in nodes:
                nodes.remove(node)
            textures = []
            for texture_slot in material.texture_slots:
                if texture_slot:
                    texture = texture_slot.texture
                    if texture:
                        if texture.type == 'IMAGE':
                            if texture.image:
                                textures.append([texture, texture_slot.uv_layer])
            if len(textures) > 1:
                self.report({'WARNING'}, 'Material "{}" has to many textures'.format(material.name))
                material.use_nodes = False
                continue
            if len(textures) == 0:
                self.report({'WARNING'}, 'Material "{}" has no textures'.format(material.name))
                material.use_nodes = False
                continue
            texture = textures[0][0]
            uv_layer = textures[0][1]
            image = texture.image
            location = [0.0, 0.0]
            uv_node = nodes.new('ShaderNodeUVMap')
            uv_node.location = location
            uv_node.uv_map = uv_layer
            uv_node.select = False
            location[0] += 300.0
            image_node = nodes.new('ShaderNodeTexImage')
            image_node.location = location
            image_node.select = False
            location[0] += 300.0
            image_node.image = image
            shader_node = nodes.new(shader_keys[self.shader_type][0])
            shader_node.location = location
            shader_node.select = False
            location[0] += 300.0
            output_node = nodes.new('ShaderNodeOutputMaterial')
            output_node.location = location
            output_node.select = False
            location[0] += 300.0
            node_tree.links.new(uv_node.outputs['UV'], image_node.inputs['Vector'])
            color_name = shader_keys[self.shader_type][1]
            output_name = shader_keys[self.shader_type][2]
            node_tree.links.new(image_node.outputs['Color'], shader_node.inputs[color_name])
            node_tree.links.new(shader_node.outputs[output_name], output_node.inputs['Surface'])
        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Changed {} material(s)'.format(len(materials)))
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_colorize_materials(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.colorize_materials'
    bl_label = 'Colorize Materials'
    bl_description = 'Set a pseudo-random diffuse color for each surface (material)'
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        default='SELECTED_OBJECTS',
        items=(
            ('ACTIVE_MATERIAL', 'Active Material', ''),
            ('ACTIVE_OBJECT', 'Active Object', ''),
            ('SELECTED_OBJECTS', 'Selected Objects', ''),
            ('ALL_OBJECTS', 'All Objects', ''),
            ('ALL_MATERIALS', 'All Materials', '')
        )
    )
    color_mode = bpy.props.EnumProperty(
        default='RANDOM_BY_MATERIAL',
        items=(
            ('RANDOM_BY_MATERIAL', 'Random by Material', ''),
            ('RANDOM_BY_MESH', 'Random by Mesh', ''),
            ('RANDOM_BY_OBJECT', 'Random by Object', ''),
            ('RANDOM_BY_ROOT', 'Random by Root', ''),
            ('SINGLE_COLOR', 'Single Color', '')
        )
    )
    change_viewport_color = bpy.props.BoolProperty(default=True)
    change_shader_color = bpy.props.BoolProperty(default=False)
    seed = bpy.props.IntProperty(min=0, max=255)
    power = bpy.props.FloatProperty(default=0.5, min=0.0, max=1.0)
    color = bpy.props.FloatVectorProperty(
        default=(0.5, 0.5, 0.5),
        size=3,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        active = self.change_viewport_color or self.change_shader_color
        column = layout.column(align=True)
        column.active = active

        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

        column.label(text='Color Mode:')
        column.prop(self, 'color_mode', expand=True)

        column.label(text='Settings:')
        is_random = self.color_mode != 'SINGLE_COLOR'

        random_column = column.column(align=True)
        random_column.active = is_random
        random_column.prop(self, 'seed', text='Seed')
        random_column.prop(self, 'power', text='Power', slider=True)

        color_column = column.column(align=True)
        color_column.active = not is_random
        color_column.prop(self, 'color', text='Color')

        column.prop(
            self,
            'change_viewport_color',
            text='Change Viewport Color'
        )
        column.prop(
            self,
            'change_shader_color',
            text='Change Shader Color'
        )

    def get_obj_mats(self, objs):
        materials = set()
        for obj in objs:
            for slot in obj.material_slots:
                mat = slot.material
                if mat:
                    materials.add((mat, obj))
        return materials

    @utils.set_cursor_state
    def execute(self, context):
        if not self.change_viewport_color and not self.change_shader_color:
            self.report({'WARNING'}, 'Nothing changed!')
            return {'FINISHED'}
        # active material
        if self.mode == 'ACTIVE_MATERIAL':
            obj = context.active_object
            mat = None
            if obj:
                mat = obj.active_material
            if not mat:
                self.report({'ERROR'}, 'No active material')
                return {'CANCELLED'}
            materials = ((mat, obj), )
        # active object
        elif self.mode == 'ACTIVE_OBJECT':
            obj = context.active_object
            if not obj:
                self.report({'ERROR'}, 'No active object')
                return {'CANCELLED'}
            objects = (obj, )
            materials = self.get_obj_mats(objects)
        # selected objects
        elif self.mode == 'SELECTED_OBJECTS':
            objects = context.selected_objects
            if not objects:
                self.report({'ERROR'}, 'No objects selected')
                return {'CANCELLED'}
            materials = self.get_obj_mats(objects)
        # all objects
        elif self.mode == 'ALL_OBJECTS':
            objects = bpy.data.objects
            if not objects:
                self.report({'ERROR'}, 'Blend-file has no objects')
                return {'CANCELLED'}
            materials = self.get_obj_mats(objects)
        # all materials
        elif self.mode == 'ALL_MATERIALS':
            all_materials = bpy.data.materials
            if not all_materials:
                self.report({'ERROR'}, 'Blend-file has no materials')
                return {'CANCELLED'}
            materials = set()
            for mat in all_materials:
                materials.add((mat, None))
        # colorize
        changed_materials_count = 0
        ctx = formats.contexts.Context()
        for mat, obj in materials:
            if self.color_mode == 'RANDOM_BY_MATERIAL':
                name = mat.name
            elif self.color_mode == 'RANDOM_BY_MESH':
                name = obj.data.name
            elif self.color_mode == 'RANDOM_BY_OBJECT':
                name = obj.name
            elif self.color_mode == 'RANDOM_BY_ROOT':
                root = utils.obj.find_root(ctx, obj)
                name = root.name
            else:
                name = None
            if name is None:
                color = list(self.color)
            else:
                data = bytearray(name, 'utf8')
                data.append(self.seed)
                hsh = zlib.crc32(data)
                color = mathutils.Color()
                color.hsv = (
                    (hsh & 0xFF) / 0xFF,
                    (((hsh >> 8) & 3) / 3 * 0.5 + 0.5) * self.power,
                    ((hsh >> 2) & 1) * (0.5 * self.power) + 0.5
                )
                color = [color.r, color.g, color.b]
            if utils.version.IS_28:
                color.append(1.0)    # alpha
            changed = False
            if self.change_viewport_color:
                mat.diffuse_color = color
                changed = True
            if self.change_shader_color:
                output_node = None
                for node in mat.node_tree.nodes:
                    if node.type == 'OUTPUT_MATERIAL':
                        if node.is_active_output:
                            output_node = node
                            break
                if output_node:
                    links = output_node.inputs['Surface'].links
                    if links:
                        link = links[0]
                        shader_node = link.from_node
                        color_socket = shader_node.inputs.get('Color')
                        if color_socket is None:
                            color_socket = shader_node.inputs.get('Base Color')
                        if color_socket:
                            color_socket.default_value = color
                            changed = True
            if changed:
                changed_materials_count += 1
        utils.draw.redraw_areas()
        self.report(
            {'INFO'},
            'Changed {} material(s)'.format(changed_materials_count)
        )
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_create_material(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.create_material'
    bl_label = 'Create X-Ray Material'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    init = False

    filter_glob = bpy.props.StringProperty(
        default='*.dds',
        options={'HIDDEN'}
    )
    directory = bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'SKIP_SAVE', 'HIDDEN'}
    )
    filepath = bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE', 'HIDDEN'}
    )
    material_name = bpy.props.StringProperty(
        options={'SKIP_SAVE', 'HIDDEN'}
    )

    def draw(self, context):    # pragma: no cover
        if not self.init:
            self.init = True

            space = context.space_data
            params = space.params
            params.display_type = 'THUMBNAIL'

            if utils.version.has_file_browser_show_tool_prop():
                space.show_region_tool_props = False

            tex_folder = utils.ie.get_tex_dirs(self)[0]

            if tex_folder:
                if isinstance(params.directory, bytes):
                    tex_folder = bytes(tex_folder, encoding='utf-8')

                if not params.directory.startswith(tex_folder):
                    params.directory = tex_folder

    def execute(self, context):
        mat = bpy.data.materials[self.material_name]
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()

        # create nodes
        loc = mathutils.Vector((0, 0))

        image_node = nodes.new('ShaderNodeTexImage')
        image_node.location = loc
        image_node.select = False
        loc.x += 450

        diffuse_node = nodes.new('ShaderNodeBsdfDiffuse')
        diffuse_node.location = loc
        diffuse_node.select = False
        loc.x += 300

        output_node = nodes.new('ShaderNodeOutputMaterial')
        output_node.location = loc
        output_node.select = False

        # create links
        mat.node_tree.links.new(
            diffuse_node.inputs['Color'],
            image_node.outputs['Color']
        )
        mat.node_tree.links.new(
            output_node.inputs['Surface'],
            diffuse_node.outputs['BSDF']
        )

        # load image
        file_path = bpy.path.abspath(self.filepath)
        image_name = os.path.basename(file_path)
        image = bpy.data.images.get(image_name)

        if image:
            image_path = bpy.path.abspath(image.filepath)
            if image_path != file_path:
                image = None

        if not image:
            image = bpy.data.images.load(file_path)

        tex_folder = utils.ie.get_tex_dirs(self)[0]

        if file_path.startswith(tex_folder):
            rel_path = file_path[len(tex_folder) : ]

            if rel_path.startswith(os.sep):
                rel_path = rel_path[1 : ]

        else:
            rel_path = image_name

        if rel_path.endswith('.dds'):
            rel_path = rel_path[ : -len('.dds')]

        image_node.image = image
        image_node.name = rel_path
        image_node.label = rel_path

        utils.draw.redraw_areas()
        self.report({'INFO'}, text.warn.ready)

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_colorize_materials,
    XRAY_OT_create_material
)
classes_27x = (
    XRAY_OT_convert_to_cycles_material,
    XRAY_OT_convert_to_internal_material,
    XRAY_OT_switch_render
)


def register():
    utils.version.register_classes(classes)
    if not utils.version.IS_28:
        utils.version.register_classes(classes_27x)


def unregister():
    if not utils.version.IS_28:
        for operator in reversed(classes_27x):
            bpy.utils.unregister_class(operator)
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
