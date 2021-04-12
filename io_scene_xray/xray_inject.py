import bpy

from .details.types import (
    XRayObjectDetailsProperties,
    XRayObjectDetailsModelProperties,
    XRayObjectDetailsSlotsProperties,
    XRayObjectDetailsSlotsLightingProperties,
    XRayObjectDetailsSlotsMeshesProperties
    )
from . import registry
from . import props


__SUBCLASSES__ = [
    XRayObjectDetailsProperties,
    XRayObjectDetailsModelProperties,
    XRayObjectDetailsSlotsProperties,
    XRayObjectDetailsSlotsLightingProperties,
    XRayObjectDetailsSlotsMeshesProperties
]

__CLASSES__ = [
    props.obj.XRayObjectProperties,
    props.mesh.XRayMeshProperties,
    props.material.XRayMaterialProperties,
    props.armature.XRayArmatureProperties,
    props.bone.XRayBoneProperties,
    props.action.XRayActionProperties,
    props.scene.XRaySceneProperties
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
