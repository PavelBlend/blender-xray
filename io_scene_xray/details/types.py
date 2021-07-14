import bpy

from . import utils
from ..version_utils import assign_props, IS_28


slots_meshes_props = {
    'mesh_0': bpy.props.StringProperty(),
    'mesh_1': bpy.props.StringProperty(),
    'mesh_2': bpy.props.StringProperty(),
    'mesh_3': bpy.props.StringProperty()
}


class XRayObjectDetailsSlotsMeshesProperties(bpy.types.PropertyGroup):
    if not IS_28:
        for prop_name, prop_value in slots_meshes_props.items():
            exec('{0} = slots_meshes_props.get("{0}")'.format(prop_name))


slots_lighting_props = {
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
    if not IS_28:
        for prop_name, prop_value in slots_lighting_props.items():
            exec('{0} = slots_lighting_props.get("{0}")'.format(prop_name))


slots_props = {
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
    if not IS_28:
        for prop_name, prop_value in slots_props.items():
            exec('{0} = slots_props.get("{0}")'.format(prop_name))


def _update_detail_color_by_index(self, context):

    if hasattr(context.object, 'xray'):
        color_indices = utils.generate_color_indices()

        context.object.xray.detail.model.color = \
            color_indices[context.object.xray.detail.model.index][0 : 3]


model_props = {
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
    if not IS_28:
        for prop_name, prop_value in model_props.items():
            exec('{0} = model_props.get("{0}")'.format(prop_name))


details_props = {
    'model': bpy.props.PointerProperty(type=XRayObjectDetailsModelProperties),
    'slots': bpy.props.PointerProperty(type=XRayObjectDetailsSlotsProperties)
}


class XRayObjectDetailsProperties(bpy.types.PropertyGroup):
    if not IS_28:
        for prop_name, prop_value in details_props.items():
            exec('{0} = details_props.get("{0}")'.format(prop_name))


classes = (
    (XRayObjectDetailsSlotsMeshesProperties, slots_meshes_props),
    (XRayObjectDetailsSlotsLightingProperties, slots_lighting_props),
    (XRayObjectDetailsSlotsProperties, slots_props),
    (XRayObjectDetailsModelProperties, model_props),
    (XRayObjectDetailsProperties, details_props),
)


def register():
    for operator, props in classes:
        assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
