from .ops import fake_bones, verify_uv, verify_uv_ui, joint_limits
from . import registry
from .ui import (
    obj, mesh, material, armature, bone, action,
    scene, view3d, collapsible, edit_helper
)


registry.module_requires(__name__, [
    collapsible,
    fake_bones,
    joint_limits,
    verify_uv.XRayVerifyUVOperator,
    verify_uv_ui.XRayVerifyToolsPanel,
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
