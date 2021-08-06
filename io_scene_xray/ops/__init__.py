from . import (
    base,
    action_utils,
    armature_utils,
    material,
    custom_props_utils,
    fake_bones,
    joint_limits,
    shader_tools,
    transform_utils,
    verify_uv,
    xray_camera
)


modules = (
    action_utils,
    armature_utils,
    material,
    custom_props_utils,
    fake_bones,
    joint_limits,
    shader_tools,
    transform_utils,
    verify_uv,
    xray_camera
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
