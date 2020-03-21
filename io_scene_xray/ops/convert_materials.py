import bpy


class MATERIAL_OT_xray_convert_to_cycles(bpy.types.Operator):
    bl_idname = 'io_scene_xray.convert_to_cycles'
    bl_label = 'Convert to Cycles'
    bl_description = ''

    def execute(self, context):
        scene = context.scene
        if scene.render.engine == 'BLENDER_RENDER':
            scene.render.engine = 'CYCLES'

        def get_object_materials(bpy_object, materials):
            for material_slot in bpy_object.material_slots:
                material = material_slot.material
                if material:
                    materials.append(material)

        mode = scene.xray.convert_materials_mode
        materials = []
        if mode == 'ACTIVE_MATERIAL':
            materials.append(context.material)
        elif mode == 'ACTIVE_OBJECT':
            get_object_materials(context.object, materials)
        elif mode == 'SELECTED_OBJECTS':
            for bpy_object in context.selected_objects:
                get_object_materials(bpy_object, materials)
        elif mode == 'ALL_MATERIALS':
            for material in bpy.data.materials:
                materials.append(material)

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
            princilped_node = nodes.new('ShaderNodeBsdfPrincipled')
            princilped_node.location = location
            location[0] += 300.0
            output_node = nodes.new('ShaderNodeOutputMaterial')
            output_node.location = location
            location[0] += 300.0
            node_tree.links.new(uv_node.outputs['UV'], image_node.inputs['Vector'])
            node_tree.links.new(image_node.outputs['Color'], princilped_node.inputs['Base Color'])
            node_tree.links.new(princilped_node.outputs['BSDF'], output_node.inputs['Surface'])
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MATERIAL_OT_xray_convert_to_cycles)


def unregister():
    bpy.utils.unregister_class(MATERIAL_OT_xray_convert_to_cycles)
