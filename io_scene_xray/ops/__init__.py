# addon modules
from . import action_utils
from . import armature_utils
from . import bone_tools
from . import material
from . import object_tools
from . import custom_props_utils
from . import fake_user_utils
from . import joint_limits
from . import shader_tools
from . import skls_browser
from . import transform_utils
from . import verify_uv
from . import xray_camera


modules = (
    action_utils,
    armature_utils,
    bone_tools,
    material,
    object_tools,
    custom_props_utils,
    fake_user_utils,
    joint_limits,
    shader_tools,
    skls_browser,
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
