import bpy

from . import registry
from . import props


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
    for clas in __CLASSES__:
        registry.register_thing(clas, __name__)
        clas.b_type.xray = bpy.props.PointerProperty(type=clas)


def unregister():
    for clas in reversed(__CLASSES__):
        del clas.b_type.xray
        registry.unregister_thing(clas, __name__)
