# addon modules
from . import obj
from . import mesh
from . import material
from . import armature
from . import bone
from . import action
from . import scene


modules = (obj, mesh, material, armature, bone, action, scene)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
