# standart modules
import zlib

# blender modules
import bpy
import mathutils

# addon modules
from .. import version_utils


def get_object_materials(bpy_object, materials):
    for material_slot in bpy_object.material_slots:
        material = material_slot.material
        if material:
            materials.add(material)


def get_materials(context, mode):
    materials = set()
    if mode == 'ACTIVE_MATERIAL':
        if not context.object:
            return materials
        if context.object.active_material:
            materials.add(context.object.active_material)
        else:
            return materials
    elif mode == 'ACTIVE_OBJECT':
        if not context.object:
            return materials
        get_object_materials(context.object, materials)
    elif mode == 'SELECTED_OBJECTS':
        for bpy_object in context.selected_objects:
            get_object_materials(bpy_object, materials)
    elif mode == 'ALL_OBJECTS':
        for bpy_object in bpy.data.objects:
            get_object_materials(bpy_object, materials)
    elif mode == 'ALL_MATERIALS':
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
            if from_node.type in version_utils.IMAGE_NODES:
                image_nodes.append(from_node)
            get_image_nodes(from_node, image_nodes)


convert_materials_mode_items = (
    ('ACTIVE_MATERIAL', 'Active Material', ''),
    ('ACTIVE_OBJECT', 'Active Object', ''),
    ('SELECTED_OBJECTS', 'Selected Objects', ''),
    ('ALL_OBJECTS', 'All Objects', ''),
    ('ALL_MATERIALS', 'All Materials', '')
)
mode_prop = bpy.props.EnumProperty(
        name='Mode',
        items=convert_materials_mode_items,
        default='ACTIVE_MATERIAL'
)

prop_mode = {
    'mode': mode_prop,
}


class XRAY_OT_switch_render(bpy.types.Operator):
    bl_idname = 'io_scene_xray.switch_render'
    bl_label = 'Switch Render'
    bl_description = 'Switch Cycles/Internal Render'
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
        for prop_name, prop_value in prop_mode.items():
            exec('{0} = prop_mode.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    def execute(self, context):
        scene = context.scene
        if scene.render.engine == 'CYCLES':
            scene.render.engine = 'BLENDER_RENDER'
        elif scene.render.engine == 'BLENDER_RENDER':
            scene.render.engine = 'CYCLES'
        else:
            scene.render.engine = 'BLENDER_RENDER'

        materials = get_materials(context, self.mode)

        if scene.render.engine == 'CYCLES':
            for material in materials:
                material.use_nodes = True
        elif scene.render.engine == 'BLENDER_RENDER':
            for material in materials:
                material.use_nodes = False

        self.report({'INFO'}, 'Changed {} material(s)'.format(len(materials)))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_convert_to_internal_material(bpy.types.Operator):
    bl_idname = 'io_scene_xray.convert_to_internal'
    bl_label = 'Convert to Internal'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
        for prop_name, prop_value in prop_mode.items():
            exec('{0} = prop_mode.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

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

        self.report({'INFO'}, 'Changed {} material(s)'.format(len(materials)))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


shader_keys = {
    'PRINCIPLED': ['ShaderNodeBsdfPrincipled', 'Base Color', 'BSDF'],
    'DIFFUSE': ['ShaderNodeBsdfDiffuse', 'Color', 'BSDF'],
    'EMISSION': ['ShaderNodeEmission', 'Color', 'Emission']
}

convert_materials_shader_type_items = (
    ('PRINCIPLED', 'Principled', ''),
    ('DIFFUSE', 'Diffuse', ''),
    ('EMISSION', 'Emission', '')
)
props = {
    'mode': mode_prop,
    'shader_type': bpy.props.EnumProperty(
        name='Shader',
        items=convert_materials_shader_type_items,
        default='PRINCIPLED'
    )
}


class XRAY_OT_convert_to_cycles_material(bpy.types.Operator):
    bl_idname = 'io_scene_xray.convert_to_cycles'
    bl_label = 'Convert to Cycles'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)
        column.label(text='Shader Type:')
        column.prop(self, 'shader_type', expand=True)

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
        self.report({'INFO'}, 'Changed {} material(s)'.format(len(materials)))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


colorize_mode_items = (
    ('ACTIVE_MATERIAL', 'Active Material', ''),
    ('ACTIVE_OBJECT', 'Active Object', ''),
    ('SELECTED_OBJECTS', 'Selected Objects', ''),
    ('ALL_OBJECTS', 'All Objects', ''),
    ('ALL_MATERIALS', 'All Materials', '')
)
xray_colorize_materials_props = {
    'mode': bpy.props.EnumProperty(
        default='SELECTED_OBJECTS',
        items=colorize_mode_items
    ),
    'change_viewport_color': bpy.props.BoolProperty(default=True),
    'change_shader_color': bpy.props.BoolProperty(default=False),
    'seed': bpy.props.IntProperty(min=0, max=255),
    'power': bpy.props.FloatProperty(default=0.5, min=0.0, max=1.0)
}


class XRAY_OT_colorize_materials(bpy.types.Operator):
    bl_idname = 'io_scene_xray.colorize_materials'
    bl_label = 'Colorize Materials'
    bl_description = 'Set a pseudo-random diffuse color for each surface (material)'
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
        for prop_name, prop_value in xray_colorize_materials_props.items():
            exec('{0} = xray_colorize_materials_props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        active = self.change_viewport_color or self.change_shader_color
        column = layout.column(align=True)
        column.active = active
        column.prop(self, 'seed', text='Seed')
        column.prop(self, 'power', text='Power', slider=True)
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
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    def get_obj_mats(self, objs):
        materials = set()
        for obj in objs:
            for slot in obj.material_slots:
                mat = slot.material
                if mat:
                    materials.add(mat)
        return materials

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
            materials = (mat, )
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
                materials.add(mat)
        # colorize
        changed_materials_count = 0
        for mat in materials:
            data = bytearray(mat.name, 'utf8')
            data.append(self.seed)
            hsh = zlib.crc32(data)
            color = mathutils.Color()
            color.hsv = (
                (hsh & 0xFF) / 0xFF,
                (((hsh >> 8) & 3) / 3 * 0.5 + 0.5) * self.power,
                ((hsh >> 2) & 1) * (0.5 * self.power) + 0.5
            )
            color = [color.r, color.g, color.b]
            if version_utils.IS_28:
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
        self.report(
            {'INFO'},
            'Changed {} material(s)'.format(changed_materials_count)
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    (XRAY_OT_convert_to_cycles_material, props),
    (XRAY_OT_convert_to_internal_material, prop_mode),
    (XRAY_OT_switch_render, prop_mode)
)


def register():
    version_utils.assign_props(
        [(xray_colorize_materials_props, XRAY_OT_colorize_materials), ]
    )
    bpy.utils.register_class(XRAY_OT_colorize_materials)
    if not version_utils.IS_28:
        for operator, props_dict in classes:
            version_utils.assign_props(
                [(props_dict, operator), ]
            )
            bpy.utils.register_class(operator)


def unregister():
    if not version_utils.IS_28:
        for operator, props in reversed(classes):
            bpy.utils.unregister_class(operator)
    bpy.utils.unregister_class(XRAY_OT_colorize_materials)
