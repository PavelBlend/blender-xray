from . import (
    base,
    action_utils,
    armature_utils,
    convert_materials,
    custom_props_utils,
    fake_bones,
    joint_limits,
    shader_tools,
    transform_utils,
    verify_uv,
    verify_uv_ui,
    xray_camera
)


modules = (
    action_utils,
    armature_utils,
    convert_materials,
    custom_props_utils,
    fake_bones,
    joint_limits,
    shader_tools,
    transform_utils,
    verify_uv,
    verify_uv_ui,
    xray_camera
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
