import bpy

from . import utils
from ..version_utils import assign_props


xray_object_details_slots_meshes_properties = {
    'mesh_0': bpy.props.StringProperty(),
    'mesh_1': bpy.props.StringProperty(),
    'mesh_2': bpy.props.StringProperty(),
    'mesh_3': bpy.props.StringProperty()
}


class XRayObjectDetailsSlotsMeshesProperties(bpy.types.PropertyGroup):
    pass


xray_object_details_slots_lighting_properties = {
    'format': bpy.props.EnumProperty(
        name='Format',
        items=(
            (
                'builds_1569-cop',
                'Builds 1569-CoP',
                'level.details version 3 (builds 1569-CoP)'
            ),
            (
                'builds_1096-1558',
                'Builds 1096-1558',
                'level.details version 2 (builds 1096-1558)'
            )
        ),
        default='builds_1569-cop'
    ),
    'lights_image': bpy.props.StringProperty(),
    'hemi_image': bpy.props.StringProperty(),
    'shadows_image': bpy.props.StringProperty()
}


class XRayObjectDetailsSlotsLightingProperties(bpy.types.PropertyGroup):
    pass


xray_object_details_slots_properties = {
    'meshes': bpy.props.PointerProperty(
        type=XRayObjectDetailsSlotsMeshesProperties
    ),
    'ligthing': bpy.props.PointerProperty(
        type=XRayObjectDetailsSlotsLightingProperties
    ),
    'meshes_object': bpy.props.StringProperty(),
    'slots_base_object': bpy.props.StringProperty(),
    'slots_top_object': bpy.props.StringProperty()
}


class XRayObjectDetailsSlotsProperties(bpy.types.PropertyGroup):
    pass


def _update_detail_color_by_index(self, context):

    if hasattr(context.object, 'xray'):
        color_indices = utils.generate_color_indices()

        context.object.xray.detail.model.color = \
            color_indices[context.object.xray.detail.model.index][0 : 3]


xray_object_details_model_properties = {
    'no_waving': bpy.props.BoolProperty(
        description='No Waving',
        options={'SKIP_SAVE'},
        default=False
    ),
    'min_scale': bpy.props.FloatProperty(default=1.0, min=0.1, max=100.0),
    'max_scale': bpy.props.FloatProperty(default=1.0, min=0.1, max=100.0),
    'index': bpy.props.IntProperty(
        default=0,
        min=0,
        max=62,
        update=_update_detail_color_by_index
    ),
    'color': bpy.props.FloatVectorProperty(
        default=(1.0, 0.0, 0.0),
        max=1.0,
        min=0.0,
        subtype='COLOR_GAMMA',
        size=3
    )
}


class XRayObjectDetailsModelProperties(bpy.types.PropertyGroup):
    pass


xray_object_details_properties = {
    'model': bpy.props.PointerProperty(type=XRayObjectDetailsModelProperties),
    'slots': bpy.props.PointerProperty(type=XRayObjectDetailsSlotsProperties)
}


class XRayObjectDetailsProperties(bpy.types.PropertyGroup):
    pass


assign_props([
    (xray_object_details_slots_meshes_properties, XRayObjectDetailsSlotsMeshesProperties),
    (xray_object_details_slots_lighting_properties, XRayObjectDetailsSlotsLightingProperties),
    (xray_object_details_slots_properties, XRayObjectDetailsSlotsProperties),
    (xray_object_details_model_properties, XRayObjectDetailsModelProperties),
    (xray_object_details_properties, XRayObjectDetailsProperties)
])
