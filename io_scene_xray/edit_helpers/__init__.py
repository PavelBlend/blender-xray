# addon modules
from . import base, bone_center, bone_shape


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
