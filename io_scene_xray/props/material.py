# blender modules
import bpy

# addon modules
from . import utility
from .. import utils


class XRayMaterialProps(utility.InitPropGroup):
    b_type = bpy.types.Material

    version = bpy.props.IntProperty()

    # general
    eshader = bpy.props.StringProperty(default='models\\model')
    cshader = bpy.props.StringProperty(default='default')
    gamemtl = bpy.props.StringProperty(default='default')

    # flags
    flags = bpy.props.IntProperty(name='flags')
    flags_twosided = utility.gen_flag_prop(mask=0x01)

    # level
    uv_texture = bpy.props.StringProperty(default='')
    uv_light_map = bpy.props.StringProperty(default='')
    lmap_0 = bpy.props.StringProperty(default='')
    lmap_1 = bpy.props.StringProperty(default='')
    light_vert_color = bpy.props.StringProperty(default='')
    sun_vert_color = bpy.props.StringProperty(default='')
    hemi_vert_color = bpy.props.StringProperty(default='')

    # cform
    suppress_shadows = bpy.props.BoolProperty()
    suppress_wm = bpy.props.BoolProperty()

    def _during_creation(self):
        obj = bpy.context.active_object

        if obj and obj.xray.flags_custom_type == 'st':
            self.eshader = 'default'


def register():
    utils.version.register_classes(XRayMaterialProps)


def unregister():
    utils.version.unregister_prop_groups(XRayMaterialProps)
