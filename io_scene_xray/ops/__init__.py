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
from . import invalid_sg
from . import joint_limits
from . import level_shaders
from . import rig
from . import shader
from . import motions_browser
from . import tests
from . import transform
from . import verify
from . import update
from . import viewer
from . import omf_editor


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
    invalid_sg,
    joint_limits,
    level_shaders,
    rig,
    shader,
    motions_browser,
    tests,
    transform,
    verify,
    update,
    viewer,
    omf_editor
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
