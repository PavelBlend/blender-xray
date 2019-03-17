
import bpy

from .details.types import (
    XRayObjectDetailsProperties,
    XRayObjectDetailsModelProperties,
    XRayObjectDetailsSlotsProperties,
    XRayObjectDetailsSlotsLightingProperties,
    XRayObjectDetailsSlotsMeshesProperties
    )
from . import registry
from . import properties


__SUBCLASSES__ = [
    XRayObjectDetailsProperties,
    XRayObjectDetailsModelProperties,
    XRayObjectDetailsSlotsProperties,
    XRayObjectDetailsSlotsLightingProperties,
    XRayObjectDetailsSlotsMeshesProperties
    ]

__CLASSES__ = [
    properties.object_.XRayObjectProperties,
    properties.mesh.XRayMeshProperties,
    properties.material.XRayMaterialProperties,
    properties.armature.XRayArmatureProperties,
    properties.bone.XRayBoneProperties,
    properties.action.XRayActionProperties,
    properties.scene.XRaySceneProperties
]


def register():
    for subclass in reversed(__SUBCLASSES__):
        registry.register_thing(subclass, __name__)
    for clas in __CLASSES__:
        registry.register_thing(clas, __name__)
        clas.b_type.xray = bpy.props.PointerProperty(type=clas)


def unregister():
    for clas in reversed(__CLASSES__):
        del clas.b_type.xray
        registry.unregister_thing(clas, __name__)
    for subclass in __SUBCLASSES__:
        registry.unregister_thing(subclass, __name__)
