# addon modules
from . import ops
from . import props
from . import ui


modules = (ops, props)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
