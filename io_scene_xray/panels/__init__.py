# addon modules
from . import action
from . import armature
from . import bone
from . import edit_helper
from . import material
from . import mesh
from . import obj
from . import scene
from . import viewport
from . import shader


modules = (
    action,
    armature,
    bone,
    edit_helper,
    material,
    mesh,
    obj,
    scene,
    viewport,
    shader
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
