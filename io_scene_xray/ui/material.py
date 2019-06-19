from . import base
from .dynamic_menu import XRayXrMenuTemplate, DynamicMenu
from ..utils import parse_shaders, parse_shaders_xrlc, parse_gamemtl
from .. import registry


@registry.requires(XRayXrMenuTemplate)
class XRayEShaderMenu(XRayXrMenuTemplate):
    bl_idname = 'io_scene_xray.dynmenu.eshader'
    prop_name = 'eshader'
    cached = XRayXrMenuTemplate.create_cached('eshader_file_auto', parse_shaders)


@registry.requires(XRayXrMenuTemplate)
class XRayCShaderMenu(XRayXrMenuTemplate):
    bl_idname = 'io_scene_xray.dynmenu.cshader'
    prop_name = 'cshader'
    cached = XRayXrMenuTemplate.create_cached('cshader_file_auto', parse_shaders_xrlc)


@registry.requires(XRayXrMenuTemplate)
class XRayGameMtlMenu(XRayXrMenuTemplate):
    bl_idname = 'io_scene_xray.dynmenu.gamemtl'
    prop_name = 'gamemtl'
    cached = XRayXrMenuTemplate.create_cached('gamemtl_file_auto', parse_gamemtl)


def _gen_xr_selector(layout, data, name, text):
    row = layout.row(align=True)
    row.prop(data, name, text=text)
    DynamicMenu.set_layout_context_data(row, data)
    row.menu('io_scene_xray.dynmenu.' + name, icon='TRIA_DOWN')


@registry.requires(XRayEShaderMenu, XRayCShaderMenu, XRayGameMtlMenu)
@registry.module_thing
class XRayMaterialPanel(base.XRayPanel):
    bl_context = 'material'
    bl_label = base.build_label('Material')

    @classmethod
    def poll(cls, context):
        return context.object.active_material

    def draw(self, context):
        layout = self.layout
        data = context.object.active_material.xray
        layout.prop(data, 'flags_twosided', 'Two sided', toggle=True)
        _gen_xr_selector(layout, data, 'eshader', 'EShader')
        _gen_xr_selector(layout, data, 'cshader', 'CShader')
        _gen_xr_selector(layout, data, 'gamemtl', 'GameMtl')
