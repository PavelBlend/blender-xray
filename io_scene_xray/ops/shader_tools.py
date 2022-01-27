# blender modules
import bpy

# addon modules
from . import material
from .. import utils
from .. import version_utils


op_props = {
    'mode': material.mode_prop,
    # alpha
    'alpha_value': bpy.props.BoolProperty(name='Use Alpha', default=True),
    'alpha_change': bpy.props.BoolProperty(name='Change Alpha', default=True),
    # specular
    'specular_value': bpy.props.FloatProperty(
        name='Specular', default=0.0, min=0.0, max=1.0, subtype='FACTOR'
    ),
    'specular_change': bpy.props.BoolProperty(name='Change Specular', default=True),
    # roughness
    'roughness_value': bpy.props.FloatProperty(
        name='Roughness', default=0.0, min=0.0, max=1.0, subtype='FACTOR'
    ),
    'roughness_change': bpy.props.BoolProperty(name='Change Roughness', default=True),
    # viewport roughness
    'viewport_roughness_value': bpy.props.FloatProperty(
        name='Viewport Roughness', default=0.0, min=0.0, max=1.0, subtype='FACTOR'
    ),
    'viewport_roughness_change': bpy.props.BoolProperty(name='Change Viewport Roughness', default=True),

    # internal properties
    'shadeless_change': bpy.props.BoolProperty(name='Change Shadeless', default=True),
    'shadeless_value': bpy.props.BoolProperty(name='Shadeless', default=True),

    'diffuse_intensity_change': bpy.props.BoolProperty(
        name='Change Diffuse Intensity', default=True
    ),
    'diffuse_intensity_value': bpy.props.FloatProperty(
        name='Diffuse Intensity', default=1.0,
        min=0.0, max=1.0, subtype='FACTOR'
    ),

    'specular_intensity_change': bpy.props.BoolProperty(
        name='Change Specular Intensity', default=True
    ),
    'specular_intensity_value': bpy.props.FloatProperty(
        name='Specular Intensity', default=1.0,
        min=0.0, max=1.0, subtype='FACTOR'
    ),

    'specular_hardness_change': bpy.props.BoolProperty(
        name='Change Specular Hardness', default=True
    ),
    'specular_hardness_value': bpy.props.IntProperty(
        name='Specular Hardness', default=50,
        min=1, max=511
    ),

    'use_transparency_change': bpy.props.BoolProperty(
        name='Change Transparency', default=True
    ),
    'use_transparency_value': bpy.props.BoolProperty(
        name='Transparency', default=True
    ),

    'transparency_alpha_change': bpy.props.BoolProperty(
        name='Change Transparency Alpha', default=True
    ),
    'transparency_alpha_value': bpy.props.FloatProperty(
        name='Transparency Alpha', default=1.0,
        min=0.0, max=1.0, subtype='FACTOR'
    )
}
renders_28x = ('CYCLES', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH')


class XRAY_OT_change_shader_params(bpy.types.Operator):
    bl_idname = 'io_scene_xray.change_shader_params'
    bl_label = 'Change Shader Parameters'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw_prop(self, layout, prop_active, prop_value):
        row = layout.row(align=True)
        row.prop(self, prop_active, text='')
        row = row.row(align=True)
        row.active = getattr(self, prop_active)
        row.prop(self, prop_value, toggle=True)

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)
        is_internal = context.scene.render.engine == 'BLENDER_RENDER'
        is_cycles = context.scene.render.engine in renders_28x
        column.label(text='Settings:')
        if is_cycles:
            self.draw_prop(column, 'specular_change', 'specular_value')
            self.draw_prop(column, 'roughness_change', 'roughness_value')
            self.draw_prop(column, 'viewport_roughness_change', 'viewport_roughness_value')
            self.draw_prop(column, 'alpha_change', 'alpha_value')
        if is_internal:
            self.draw_prop(column, 'diffuse_intensity_change', 'diffuse_intensity_value')
            self.draw_prop(column, 'specular_intensity_change', 'specular_intensity_value')
            self.draw_prop(column, 'transparency_alpha_change', 'transparency_alpha_value')
            self.draw_prop(column, 'specular_hardness_change', 'specular_hardness_value')
            self.draw_prop(column, 'use_transparency_change', 'use_transparency_value')
            self.draw_prop(column, 'shadeless_change', 'shadeless_value')

    @utils.set_cursor_state
    def execute(self, context):
        scene = context.scene
        materials = material.get_materials(context, self.mode)
        is_cycles = scene.render.engine in renders_28x
        is_internal = scene.render.engine == 'BLENDER_RENDER'
        for mat in materials:
            if is_cycles:
                if not mat.node_tree:
                    continue
                output_node = None
                for node in mat.node_tree.nodes:
                    if node.type == 'OUTPUT_MATERIAL':
                        if node.is_active_output:
                            output_node = node
                            break
                if self.viewport_roughness_change:
                    mat.roughness = self.viewport_roughness_value
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
                if self.specular_change:
                    shader_node.inputs['Specular'].default_value = self.specular_value
                if self.roughness_change:
                    shader_node.inputs['Roughness'].default_value = self.roughness_value
                if not self.alpha_change:
                    continue
                links = shader_node.inputs['Base Color'].links
                if not len(links):
                    self.report({'WARNING'}, 'Material "{}" has no texture.'.format(mat.name))
                    continue
                image_node = links[0].from_node
                if not image_node.type in version_utils.IMAGE_NODES:
                    self.report({'WARNING'}, 'Material "{}" has no image.'.format(mat.name))
                    continue
                if version_utils.IS_28:
                    if self.alpha_value:
                        mat.node_tree.links.new(
                            image_node.outputs['Alpha'],
                            shader_node.inputs['Alpha']
                        )
                    else:
                        links = shader_node.inputs['Alpha'].links
                        if len(links):
                            mat.node_tree.links.remove(links[0])
            if is_internal:
                # shadeless
                if self.shadeless_change:
                    mat.use_shadeless = self.shadeless_value
                # diffuse intensity
                if self.diffuse_intensity_change:
                    mat.diffuse_intensity = self.diffuse_intensity_value
                # specular intensity
                if self.specular_intensity_change:
                    mat.specular_intensity = self.specular_intensity_value
                # specular hardness
                if self.specular_hardness_change:
                    mat.specular_hardness = self.specular_hardness_value
                # use transparency
                if self.use_transparency_change:
                    mat.use_transparency = self.use_transparency_value
                # transparency alpha
                if self.transparency_alpha_change:
                    mat.alpha = self.transparency_alpha_value
            mat.update_tag()
        self.report({'INFO'}, 'Changed {} material(s)'.format(len(materials)))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    version_utils.register_operators(XRAY_OT_change_shader_params)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_change_shader_params)
