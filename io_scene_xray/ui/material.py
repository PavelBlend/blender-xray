from . import base, collapsible
from .dynamic_menu import XRayXrMenuTemplate, DynamicMenu
from ..utils import parse_shaders, parse_shaders_xrlc, parse_gamemtl
from ..version_utils import IS_28
from .. import registry


@registry.requires(XRayXrMenuTemplate)
class XRayEShaderMenu(XRayXrMenuTemplate):
    bl_idname = 'XRAY_MT_EShaderMenu'
    prop_name = 'eshader'
    cached = XRayXrMenuTemplate.create_cached('eshader_file_auto', parse_shaders)


@registry.requires(XRayXrMenuTemplate)
class XRayCShaderMenu(XRayXrMenuTemplate):
    bl_idname = 'XRAY_MT_CShaderMenu'
    prop_name = 'cshader'
    cached = XRayXrMenuTemplate.create_cached('cshader_file_auto', parse_shaders_xrlc)


@registry.requires(XRayXrMenuTemplate)
class XRayGameMtlMenu(XRayXrMenuTemplate):
    bl_idname = 'XRAY_MT_GameMtlMenu'
    prop_name = 'gamemtl'
    cached = XRayXrMenuTemplate.create_cached('gamemtl_file_auto', parse_gamemtl)


def _gen_xr_selector(layout, data, name, text):
    row = layout.row(align=True)
    row.prop(data, name, text=text)
    DynamicMenu.set_layout_context_data(row, data)
    row.menu('XRAY_MT_{}Menu'.format(text), icon='TRIA_DOWN')


@registry.requires(XRayEShaderMenu, XRayCShaderMenu, XRayGameMtlMenu)
@registry.module_thing
class XRAY_PT_MaterialPanel(base.XRayPanel):
    bl_context = 'material'
    bl_label = base.build_label('Material')

    @classmethod
    def poll(cls, context):
        return context.object.active_material

    def draw(self, context):
        layout = self.layout
        material = context.object.active_material
        data = material.xray
        layout.prop(data, 'flags_twosided', text='Two sided', toggle=True)
        _gen_xr_selector(layout, data, 'eshader', 'EShader')
        _gen_xr_selector(layout, data, 'cshader', 'CShader')
        _gen_xr_selector(layout, data, 'gamemtl', 'GameMtl')
        collapsible_text = 'Converter'
        if IS_28:
            def draw_level_prop(prop_name, prop_text, light_type='LMAP'):
                row = box.split(factor=0.45)
                row.label(text=prop_text)
                if light_type == 'LMAP':
                    row.prop_search(data, prop_name, material.node_tree, 'nodes', text='')
                else:
                    row.prop_search(data, prop_name, context.object.data, 'vertex_colors', text='')
            box = layout.box()
            box.label(text='Level CForm:')
            box.prop(data, 'suppress_shadows', text='Suppress Shadows')
            box.prop(data, 'suppress_wm', text='Suppress Wallmarks')
            box = layout.box()
            box.label(text='Level Visual:')
            draw_level_prop('lmap_0', 'Light Map 1:')
            draw_level_prop('lmap_1', 'Light Map 2:')
            draw_level_prop('light_vert_color', 'Light Vertex Color:', light_type='VERTEX')
            draw_level_prop('sun_vert_color', 'Sun Vertex Color:', light_type='VERTEX')
            draw_level_prop('hemi_vert_color', 'Hemi Vertex Color:', light_type='VERTEX')
            collapsible_text = 'Utils'
        row, box = collapsible.draw(
            layout, 'test_key', text='Material {0}'.format(collapsible_text)
        )
        if box:
            box.prop(context.scene.xray, 'convert_materials_mode')
            if not IS_28:
                box.prop(context.scene.xray, 'convert_materials_shader_type')
                box.operator('io_scene_xray.convert_to_cycles')
                box.operator('io_scene_xray.convert_to_internal')
                if context.scene.render.engine == 'CYCLES':
                    text = 'Switch Render (Internal)'
                elif context.scene.render.engine == 'BLENDER_RENDER':
                    text = 'Switch Render (Cycles)'
                box.operator('io_scene_xray.switch_render', text=text)
            else:
                box.prop(context.scene.xray, 'materials_set_alpha_mode')
                box.operator('io_scene_xray.set_texture_alpha')
