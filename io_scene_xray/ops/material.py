# blender modules
import bpy
from mathutils import Color

# addon modules
from ..version_utils import IS_28, IMAGE_NODES, assign_props
from .. import utils


def get_object_materials(bpy_object, materials):
    for material_slot in bpy_object.material_slots:
        material = material_slot.material
        if material:
            materials.append(material)


def get_materials(context, scene):
    mode = scene.xray.convert_materials_mode
    materials = []
    if mode == 'ACTIVE_MATERIAL':
        if not context.object:
            return materials
        if context.object.active_material:
            materials.append(context.object.active_material)
        else:
            return materials
    elif mode == 'ACTIVE_OBJECT':
        if not context.object:
            return materials
        get_object_materials(context.object, materials)
    elif mode == 'SELECTED_OBJECTS':
        for bpy_object in context.selected_objects:
            get_object_materials(bpy_object, materials)
    elif mode == 'ALL_MATERIALS':
        for material in bpy.data.materials:
            materials.append(material)
    return materials


def get_image_nodes(node, image_nodes):
    for node_input in node.inputs:
        from_node = None
        for link in node_input.links:
            from_node = link.from_node
            break
        if from_node:
            if from_node.type in IMAGE_NODES:
                image_nodes.append(from_node)
            get_image_nodes(from_node, image_nodes)


class XRAY_OT_xray_switch_render(bpy.types.Operator):
    bl_idname = 'io_scene_xray.switch_render'
    bl_label = 'Switch Render'
    bl_description = 'Switch Cycles/Internal Render'

    def execute(self, context):
        scene = context.scene
        if scene.render.engine == 'CYCLES':
            scene.render.engine = 'BLENDER_RENDER'
        elif scene.render.engine == 'BLENDER_RENDER':
            scene.render.engine = 'CYCLES'

        materials = get_materials(context, scene)

        if scene.render.engine == 'CYCLES':
            for material in materials:
                material.use_nodes = True
        elif scene.render.engine == 'BLENDER_RENDER':
            for material in materials:
                material.use_nodes = False

        return {'FINISHED'}


class XRAY_OT_xray_convert_to_internal_material(bpy.types.Operator):
    bl_idname = 'io_scene_xray.convert_to_internal'
    bl_label = 'Convert to Internal'
    bl_description = ''

    def execute(self, context):
        scene = context.scene
        if scene.render.engine != 'CYCLES':
            return {'FINISHED'}

        materials = get_materials(context, scene)

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

        scene.render.engine = 'BLENDER_RENDER'
        return {'FINISHED'}


shader_keys = {
    'PRINCIPLED': ['ShaderNodeBsdfPrincipled', 'Base Color', 'BSDF'],
    'DIFFUSE': ['ShaderNodeBsdfDiffuse', 'Color', 'BSDF'],
    'EMISSION': ['ShaderNodeEmission', 'Color', 'Emission']
}


class XRAY_OT_xray_convert_to_cycles_material(bpy.types.Operator):
    bl_idname = 'io_scene_xray.convert_to_cycles'
    bl_label = 'Convert to Cycles'
    bl_description = ''

    def execute(self, context):
        scene = context.scene
        if scene.render.engine == 'BLENDER_RENDER':
            scene.render.engine = 'CYCLES'

        materials = get_materials(context, scene)

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
            shader_node = nodes.new(shader_keys[scene.xray.convert_materials_shader_type][0])
            shader_node.location = location
            shader_node.select = False
            location[0] += 300.0
            output_node = nodes.new('ShaderNodeOutputMaterial')
            output_node.location = location
            output_node.select = False
            location[0] += 300.0
            node_tree.links.new(uv_node.outputs['UV'], image_node.inputs['Vector'])
            color_name = shader_keys[scene.xray.convert_materials_shader_type][1]
            output_name = shader_keys[scene.xray.convert_materials_shader_type][2]
            node_tree.links.new(image_node.outputs['Color'], shader_node.inputs[color_name])
            node_tree.links.new(shader_node.outputs[output_name], output_node.inputs['Surface'])
        return {'FINISHED'}


xray_colorize_materials_props = {
    'seed': bpy.props.IntProperty(min=0, max=255),
    'power': bpy.props.FloatProperty(default=0.5, min=0.0, max=1.0)
}


class XRAY_OT_colorize_materials(bpy.types.Operator):
    bl_idname = 'io_scene_xray.colorize_materials'
    bl_label = 'Colorize Materials'
    bl_description = 'Set a pseudo-random diffuse color for each surface (material)'

    if not IS_28:
        for prop_name, prop_value in xray_colorize_materials_props.items():
            exec('{0} = xray_colorize_materials_props.get("{0}")'.format(prop_name))

    def execute(self, context):
        from zlib import crc32

        objects = context.selected_objects
        if not objects:
            self.report({'ERROR'}, 'No objects selected')
            return {'CANCELLED'}

        xr_data = context.scene.xray
        self.seed = xr_data.materials_colorize_random_seed
        self.power = xr_data.materials_colorize_color_power
        materials = set()
        for obj in objects:
            for slot in obj.material_slots:
                materials.add(slot.material)

        for mat in materials:
            if not mat:
                continue
            data = bytearray(mat.name, 'utf8')
            data.append(self.seed)
            hsh = crc32(data)
            color = Color()
            color.hsv = (
                (hsh & 0xFF) / 0xFF,
                (((hsh >> 8) & 3) / 3 * 0.5 + 0.5) * self.power,
                ((hsh >> 2) & 1) * (0.5 * self.power) + 0.5
            )
            color = [color.r, color.g, color.b]
            if IS_28:
                color.append(1.0)    # alpha
            mat.diffuse_color = color
        return {'FINISHED'}


classes = (
    XRAY_OT_xray_convert_to_cycles_material,
    XRAY_OT_xray_convert_to_internal_material,
    XRAY_OT_xray_switch_render
)


def register():
    assign_props([(xray_colorize_materials_props, XRAY_OT_colorize_materials), ])
    bpy.utils.register_class(XRAY_OT_colorize_materials)
    if not IS_28:
        for operator in classes:
            bpy.utils.register_class(operator)


def unregister():
    if not IS_28:
        for operator in reversed(classes):
            bpy.utils.unregister_class(operator)
    bpy.utils.unregister_class(XRAY_OT_colorize_materials)
