from . import registry
from .ui import (
    obj, mesh, material, armature, bone, action,
    scene, view3d, collapsible, edit_helper
)


registry.module_requires(__name__, [
    collapsible,
    obj,
    mesh,
    material,
    armature,
    bone,
    action, 
    scene,
    view3d,
    edit_helper
])
