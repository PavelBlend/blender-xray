# blender modules
import bpy

# addon modules
from . import material
from .. import utils


if utils.version.support_principled_shader():
    shader_items = (
        ('ShaderNodeBsdfDiffuse', 'Diffuse', ''),
        ('ShaderNodeEmission', 'Emission', ''),
        ('ShaderNodeBsdfPrincipled', 'Principled', '')
    )
    default_shader = 'ShaderNodeBsdfPrincipled'
else:
    shader_items = (
        ('ShaderNodeBsdfDiffuse', 'Diffuse', ''),
        ('ShaderNodeEmission', 'Emission', '')
    )
    default_shader = 'ShaderNodeBsdfDiffuse'

if utils.version.IS_28:
    blend_mode_items = (
        ('OPAQUE', 'Opaque', ''),
        ('CLIP', 'Alpha Clip', ''),
        ('HASHED', 'Alpha Hashed', ''),
        ('BLEND', 'Alpha Blend', ''),
    )
else:
    blend_mode_items = (
        ('OPAQUE', 'Opaque', ''),
        ('ADD', 'Add', ''),
        ('CLIP', 'Alpha Clip', ''),
        ('ALPHA', 'Alpha Blend', ''),
        ('ALPHA_SORT', 'Alpha Sort', ''),
        ('ALPHA_ANTIALIASING', 'Alpha Anti-Aliasing', '')
    )

shadow_mode_items = (
    ('NONE', 'None', ''),
    ('OPAQUE', 'Opaque', ''),
    ('CLIP', 'Alpha Clip', ''),
    ('HASHED', 'Alpha Hashed', '')
)

renders_28x = ('CYCLES', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH')


class XRAY_OT_change_shader_params(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.change_shader_params'
    bl_label = 'Change Shader Parameters'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    mode = material.mode_prop

    # cycles properties

    # alpha
    alpha_value = bpy.props.BoolProperty(name='Use Alpha', default=True)
    alpha_change = bpy.props.BoolProperty(name='Change Alpha', default=True)

    # specular
    specular_value = bpy.props.FloatProperty(
        name='Specular',
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    specular_change = bpy.props.BoolProperty(
        name='Change Specular',
        default=True
    )

    # roughness
    roughness_value = bpy.props.FloatProperty(
        name='Roughness',
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    roughness_change = bpy.props.BoolProperty(
        name='Change Roughness',
        default=True
    )

    # viewport roughness
    viewport_roughness_value = bpy.props.FloatProperty(
        name='Viewport Roughness',
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    viewport_roughness_change = bpy.props.BoolProperty(
        name='Change Viewport Roughness',
        default=True
    )

    # shader
    shader_value = bpy.props.EnumProperty(
        name='Shader Type',
        default=default_shader,
        items=shader_items
    )
    shader_change = bpy.props.BoolProperty(
        name='Replace Shader',
        default=False
    )

    # blend mode
    blend_mode_value = bpy.props.EnumProperty(
        name='Blend Mode',
        default='OPAQUE',
        items=blend_mode_items
    )
    blend_mode_change = bpy.props.BoolProperty(
        name='Change Blend Mode',
        default=False
    )

    # shadow mode
    shadow_mode_value = bpy.props.EnumProperty(
        name='Shadow Mode',
        default='OPAQUE',
        items=shadow_mode_items
    )
    shadow_mode_change = bpy.props.BoolProperty(
        name='Change Shadow Mode',
        default=False
    )

    # internal properties

    # shadeless
    shadeless_change = bpy.props.BoolProperty(
        name='Change Shadeless',
        default=True
    )
    shadeless_value = bpy.props.BoolProperty(
        name='Shadeless',
        default=True
    )

    # diffuse intensity
    diffuse_intensity_change = bpy.props.BoolProperty(
        name='Change Diffuse Intensity',
        default=True
    )
    diffuse_intensity_value = bpy.props.FloatProperty(
        name='Diffuse Intensity',
        default=1.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )

    # specular intensity
    specular_intensity_change = bpy.props.BoolProperty(
        name='Change Specular Intensity',
        default=True
    )
    specular_intensity_value = bpy.props.FloatProperty(
        name='Specular Intensity',
        default=1.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )

    # specular hardness
    specular_hardness_change = bpy.props.BoolProperty(
        name='Change Specular Hardness',
        default=True
    )
    specular_hardness_value = bpy.props.IntProperty(
        name='Specular Hardness',
        default=50,
        min=1,
        max=511
    )

    # transparency
    use_transparency_change = bpy.props.BoolProperty(
        name='Change Transparency',
        default=True
    )
    use_transparency_value = bpy.props.BoolProperty(
        name='Transparency',
        default=True
    )

    # transparency alpha
    transparency_alpha_change = bpy.props.BoolProperty(
        name='Change Transparency Alpha',
        default=True
    )
    transparency_alpha_value = bpy.props.FloatProperty(
        name='Transparency Alpha',
        default=1.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )

    def _draw_prop(self, layout, prop):    # pragma: no cover
        # properties names
        prop_active = prop + '_change'
        prop_value = prop + '_value'

        # layout
        row = layout.row(align=True)

        # change
        row.prop(self, prop_active, text='')

        # value
        row = row.row(align=True)
        row.active = getattr(self, prop_active)
        row.prop(self, prop_value, toggle=True)

    def _get_render_status(self, context):
        is_cycles = context.scene.render.engine in renders_28x
        is_internal = context.scene.render.engine == 'BLENDER_RENDER'

        return is_cycles, is_internal

    def draw(self, context):    # pragma: no cover
        is_cycles, is_internal = self._get_render_status(context)

        # layout
        column = self.layout.column(align=True)

        # mode
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

        # settings
        column.label(text='Settings:')

        # cycles render
        if is_cycles:
            self._draw_prop(column, 'specular')
            self._draw_prop(column, 'roughness')
            self._draw_prop(column, 'viewport_roughness')

            if utils.version.IS_28:
                self._draw_prop(column, 'alpha')

            self._draw_prop(column, 'shader')
            self._draw_prop(column, 'blend_mode')

            if utils.version.IS_28:
                self._draw_prop(column, 'shadow_mode')

        # internal render
        if is_internal:
            self._draw_prop(column, 'diffuse_intensity')
            self._draw_prop(column, 'specular_intensity')
            self._draw_prop(column, 'transparency_alpha')
            self._draw_prop(column, 'specular_hardness')
            self._draw_prop(column, 'use_transparency')
            self._draw_prop(column, 'shadeless')

    def _change_cycles_params(self, mat):
        if not mat.node_tree:
            return

        # search output node
        output_node = None
        for node in mat.node_tree.nodes:
            if node.type == 'OUTPUT_MATERIAL':
                if node.is_active_output:
                    output_node = node
                    break

        # viewport roughness
        if self.viewport_roughness_change:
            mat.roughness = self.viewport_roughness_value

        # blend mode
        if self.blend_mode_change:
            if utils.version.IS_28:
                mat.blend_method = self.blend_mode_value
            else:
                mat.game_settings.alpha_blend = self.blend_mode_value

        # shadow mode
        if self.shadow_mode_change:
            if utils.version.IS_28:
                mat.shadow_method = self.shadow_mode_value

        if not output_node:
            self.report(
                {'WARNING'},
                'Material "{}" has no output node.'.format(mat.name)
            )
            return

        links = output_node.inputs['Surface'].links
        if not len(links):
            self.report(
                {'WARNING'},
                'Material "{}" has no shader.'.format(mat.name)
            )
            return

        # change shader
        shader_node = links[0].from_node

        if self.shader_change and self.shader_value != shader_node.bl_idname:

            # create new shader node
            new_shader = mat.node_tree.nodes.new(self.shader_value)
            new_shader.location = shader_node.location
            new_shader.label = shader_node.label
            new_shader.color = shader_node.color
            new_shader.select = shader_node.select
            new_shader.use_custom_color = shader_node.use_custom_color

            # search color input
            color_socket = new_shader.inputs.get('Base Color')
            if not color_socket:
                color_socket = new_shader.inputs.get('Color')

            if color_socket:

                # search old color input
                old_input = shader_node.inputs.get('Base Color')
                if not old_input:
                    old_input = shader_node.inputs.get('Color')

                # create new color link
                if old_input and old_input.links:
                    color_input = old_input.links[0].from_socket
                    mat.node_tree.links.new(
                        color_input,
                        color_socket
                    )

            # search shader output
            if self.shader_value != 'ShaderNodeEmission':
                bsdf_socket = new_shader.outputs.get('BSDF')
            else:
                bsdf_socket = new_shader.outputs.get('Emission')

            # create output link
            output_surface = output_node.inputs.get('Surface')
            if bsdf_socket and output_surface:
                mat.node_tree.links.new(
                    output_surface,
                    bsdf_socket
                )

            # remove preview shader node
            mat.node_tree.nodes.remove(shader_node)
            shader_node = new_shader

        if shader_node.type != 'BSDF_PRINCIPLED':
            self.report(
                {'WARNING'},
                'Material "{}" has no principled shader.'.format(mat.name)
            )
            return

        # specular
        if self.specular_change:
            spec_input = shader_node.inputs['Specular']
            spec_input.default_value = self.specular_value

        # roughness change
        if self.roughness_change:
            rough_input = shader_node.inputs['Roughness']
            rough_input.default_value = self.roughness_value

        if not self.alpha_change:
            return

        links = shader_node.inputs['Base Color'].links
        if not len(links):
            self.report(
                {'WARNING'},
                'Material "{}" has no texture.'.format(mat.name)
            )
            return

        image_node = links[0].from_node
        if not image_node.type in utils.version.IMAGE_NODES:
            self.report(
                {'WARNING'},
                'Material "{}" has no image.'.format(mat.name)
            )
            return

        # change alpha
        if utils.version.IS_28:

            # create link
            if self.alpha_value:
                mat.node_tree.links.new(
                    image_node.outputs['Alpha'],
                    shader_node.inputs['Alpha']
                )

            # remove link
            else:
                links = shader_node.inputs['Alpha'].links
                if len(links):
                    mat.node_tree.links.remove(links[0])

    def _change_internal_params(self, mat):
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

    @utils.set_cursor_state
    def execute(self, context):
        mats = material.get_materials(context, self.mode)
        mats_count = len(mats)
        is_cycles, is_internal = self._get_render_status(context)

        if is_cycles:
            funct = self._change_cycles_params

        if is_internal:
            funct = self._change_internal_params

        for mat in mats:
            funct(mat)
            mat.update_tag()

        utils.draw.redraw_areas()
        self.report({'INFO'}, 'Changed {} material(s)'.format(mats_count))

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    utils.version.register_classes(XRAY_OT_change_shader_params)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_change_shader_params)
