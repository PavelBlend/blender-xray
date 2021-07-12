import bpy

from ..version_utils import IS_28
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
            if from_node.type in utils.IMAGE_NODES:
                image_nodes.append(from_node)
            get_image_nodes(from_node, image_nodes)


class MATERIAL_OT_xray_switch_render(bpy.types.Operator):
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


class MATERIAL_OT_xray_convert_to_internal(bpy.types.Operator):
    bl_idname = 'io_scene_xray.convert_to_internal'
    bl_label = 'Convert to Internal'
    bl_description = ''

    def execute(self, context):
        scene = context.scene
        if scene.render.engine == 'CYCLES':
            scene.render.engine = 'BLENDER_RENDER'

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

        return {'FINISHED'}


shader_keys = {
    'PRINCIPLED': ['ShaderNodeBsdfPrincipled', 'Base Color', 'BSDF'],
    'DIFFUSE': ['ShaderNodeBsdfDiffuse', 'Color', 'BSDF'],
    'EMISSION': ['ShaderNodeEmission', 'Color', 'Emission']
}

class MATERIAL_OT_xray_convert_to_cycles(bpy.types.Operator):
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
            location[0] += 300.0
            image_node = nodes.new('ShaderNodeTexImage')
            image_node.location = location
            location[0] += 300.0
            image_node.image = image
            shader_node = nodes.new(shader_keys[scene.xray.convert_materials_shader_type][0])
            shader_node.location = location
            location[0] += 300.0
            output_node = nodes.new('ShaderNodeOutputMaterial')
            output_node.location = location
            location[0] += 300.0
            node_tree.links.new(uv_node.outputs['UV'], image_node.inputs['Vector'])
            color_name = shader_keys[scene.xray.convert_materials_shader_type][1]
            output_name = shader_keys[scene.xray.convert_materials_shader_type][2]
            node_tree.links.new(image_node.outputs['Color'], shader_node.inputs[color_name])
            node_tree.links.new(shader_node.outputs[output_name], output_node.inputs['Surface'])
        return {'FINISHED'}


classes = (
    MATERIAL_OT_xray_convert_to_cycles,
    MATERIAL_OT_xray_convert_to_internal,
    MATERIAL_OT_xray_switch_render
)


def register():
    if not IS_28:
        for operator in classes:
            bpy.utils.register_class(operator)


def unregister():
    if not IS_28:
        for operator in reversed(classes):
            bpy.utils.unregister_class(operator)
