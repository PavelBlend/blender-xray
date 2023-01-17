# addon modules
from . import action
from . import add
from . import armature
from . import bone
from . import edit_helpers
from . import material
from . import obj
from . import props_tools
from . import custom_props
from . import fake_user
from . import joint_limits
from . import rig
from . import shader
from . import skls_browser
from . import tests
from . import transform
from . import verify
from . import update
from . import viewer


modules = (
    action,
    add,
    armature,
    bone,
    edit_helpers,
    material,
    obj,
    props_tools,
    custom_props,
    fake_user,
    joint_limits,
    rig,
    shader,
    skls_browser,
    tests,
    transform,
    verify,
    update,
    viewer
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
