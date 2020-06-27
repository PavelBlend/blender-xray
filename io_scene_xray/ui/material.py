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
        data = context.object.active_material.xray
        layout.prop(data, 'flags_twosided', text='Two sided', toggle=True)
        _gen_xr_selector(layout, data, 'eshader', 'EShader')
        _gen_xr_selector(layout, data, 'cshader', 'CShader')
        _gen_xr_selector(layout, data, 'gamemtl', 'GameMtl')
        if IS_28:
            layout.label(text='Suppress:')
            layout.prop(data, 'suppress_shadows', text='Shadows')
            layout.prop(data, 'suppress_wm', text='Wallmarks')
