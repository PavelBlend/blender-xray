# addon modules
from . import connect_bones


modules = (connect_bones, )


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
