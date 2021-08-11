# addon modules
from . import ops
from . import types


modules = (types, ops)


def register():
    for module in modules:
        module.register()


def unregister():
    modules = (types, ops)
    for module in reversed(modules):
        module.unregister()
