# addon modules
from . import action
from . import armature
from . import bone
from . import material
from . import mesh
from . import obj
from . import scene
from . import view3d
from . import shader_editor


modules = (
    action,
    armature,
    bone,
    material,
    mesh,
    obj,
    scene,
    view3d,
    shader_editor
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
