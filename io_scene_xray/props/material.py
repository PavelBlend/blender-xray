# blender modules
import bpy

# addon modules
from . import utility
from .. import utils


xray_material_properties = {
    'flags': bpy.props.IntProperty(name='flags'),
    'flags_twosided': utility.gen_flag_prop(mask=0x01),
    'eshader': bpy.props.StringProperty(default='models\\model'),
    'cshader': bpy.props.StringProperty(default='default'),
    'gamemtl': bpy.props.StringProperty(default='default'),
    'version': bpy.props.IntProperty(),
    'uv_texture': bpy.props.StringProperty(default=''),
    'uv_light_map': bpy.props.StringProperty(default=''),
    'lmap_0': bpy.props.StringProperty(default=''),
    'lmap_1': bpy.props.StringProperty(default=''),
    'light_vert_color': bpy.props.StringProperty(default=''),
    'sun_vert_color': bpy.props.StringProperty(default=''),
    'hemi_vert_color': bpy.props.StringProperty(default=''),
    'suppress_shadows': bpy.props.BoolProperty(),
    'suppress_wm': bpy.props.BoolProperty()
}


class XRayMaterialProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Material

    if not utils.version.IS_28:
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


prop_groups = (
    (XRayMaterialProperties, xray_material_properties),
)


def register():
    for prop_group, props in prop_groups:
        utils.version.assign_props([
            (props, prop_group),
        ])
    bpy.utils.register_class(prop_group)
    prop_group.b_type.xray = bpy.props.PointerProperty(type=prop_group)


def unregister():
    for prop_group, props in reversed(prop_groups):
        del prop_group.b_type.xray
        bpy.utils.unregister_class(prop_group)
