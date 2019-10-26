import bpy

from . import utils
from ..version_utils import assign_props, IS_28


xray_material_properties = {
    'flags': bpy.props.IntProperty(name='flags'),
    'flags_twosided': utils.gen_flag_prop(mask=0x01),
    'eshader': bpy.props.StringProperty(default='models\\model'),
    'cshader': bpy.props.StringProperty(default='default'),
    'gamemtl': bpy.props.StringProperty(default='default'),
    'version': bpy.props.IntProperty(),
    'suppress_shadows': bpy.props.BoolProperty(),
    'suppress_wm': bpy.props.BoolProperty()
}


class XRayMaterialProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Material

    if not IS_28:
        for prop_name, prop_value in xray_material_properties.items():
            exec('{0} = xray_material_properties.get("{0}")'.format(prop_name))

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
