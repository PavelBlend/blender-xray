import bpy

from . import material
from .. import version_utils


class MATERIAL_OT_change_shader_params(bpy.types.Operator):
    bl_idname = 'io_scene_xray.change_shader_params'
    bl_label = 'Change Shader Parameters'
    bl_description = ''

    def execute(self, context):
        scene = context.scene
        materials = material.get_materials(context, scene)
        for mat in materials:
            if not mat.node_tree:
                continue
            output_node = None
            for node in mat.node_tree.nodes:
                if node.type == 'OUTPUT_MATERIAL':
                    if node.is_active_output:
                        output_node = node
                        break
            if not output_node:
                self.report({'WARNING'}, 'Material "{}" has no output node.'.format(mat.name))
                continue
            links = output_node.inputs['Surface'].links
            if not len(links):
                self.report({'WARNING'}, 'Material "{}" has no shader.'.format(mat.name))
                continue
            shader_node = links[0].from_node
            if shader_node.type != 'BSDF_PRINCIPLED':
                self.report({'WARNING'}, 'Material "{}" has no principled shader.'.format(mat.name))
                continue
            if scene.xray.change_specular:
                shader_node.inputs['Specular'].default_value = scene.xray.shader_specular_value
            if scene.xray.change_roughness:
                shader_node.inputs['Roughness'].default_value = scene.xray.shader_roughness_value
            links = shader_node.inputs['Base Color'].links
            if not len(links):
                self.report({'WARNING'}, 'Material "{}" has no texture.'.format(mat.name))
                continue
            image_node = links[0].from_node
            if not image_node.type in version_utils.IMAGE_NODES:
                self.report({'WARNING'}, 'Material "{}" has no image.'.format(mat.name))
                continue
            if scene.xray.change_materials_alpha and version_utils.IS_28:
                if scene.xray.materials_set_alpha_mode:
                    mat.node_tree.links.new(
                        image_node.outputs['Alpha'],
                        shader_node.inputs['Alpha']
                    )
                else:
                    links = shader_node.inputs['Alpha'].links
                    if len(links):
                        mat.node_tree.links.remove(links[0])
            mat.update_tag()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MATERIAL_OT_change_shader_params)


def unregister():
    bpy.utils.unregister_class(MATERIAL_OT_change_shader_params)
