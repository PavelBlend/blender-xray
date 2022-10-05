# addon modules
from . import base
from . import bone_center
from . import bone_shape


modules = (
    base,
    bone_center,
    bone_shape
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
