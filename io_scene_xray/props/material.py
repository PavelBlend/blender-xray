import bpy

from . import utils
from ..version_utils import assign_props


xray_material_properties = {
    'flags': bpy.props.IntProperty(name='flags'),
    'flags_twosided': utils.gen_flag_prop(mask=0x01),
    'eshader': bpy.props.StringProperty(default='models\\model'),
    'cshader': bpy.props.StringProperty(default='default'),
    'gamemtl': bpy.props.StringProperty(default='default'),
    'version': bpy.props.IntProperty()
}


class XRayMaterialProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Material

    def initialize(self, context):
        if not self.version:
            if context.operation == 'LOADED':
                self.version = -1
            elif context.operation == 'CREATED':
                self.version = context.plugin_version_number
                obj = bpy.context.active_object
                if obj and obj.xray.flags_custom_type == 'st':
                    self.eshader = 'default'


assign_props([
    (xray_material_properties, XRayMaterialProperties),
])
